#ifdef EXT_PYTHON
#include <Python.h>
#endif

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <strings.h>

#include <new>
#include <vector>
#include <sstream>
#include <iostream>
#include <iterator>
#include <algorithm>

#include <papi.h>
#include "sqlite3.h"

#ifdef WITH_CUPTI
#include <cupti.h>
#include <cuda.h>
#include <cuda_runtime_api.h>
#endif // WITH_CUPTI

using namespace std;

#define  XSTR(s) _XSTR(s)
#define _XSTR(s) #s

#ifdef EXT_PYTHON
static PyObject *PartError;
#endif

static void
report_error(const char *msg, const char *extra, const char *lineno)
{
    string str;

    str += msg;

    if (extra) {
	str += ": ";
	str += extra;
    }

    str += " (";
    str += __FILE__;
    str += ":";
    str += lineno;
    str += ")";

#ifdef EXT_PYTHON
    // set exception
    PyErr_SetString(PartError, str.c_str());
#else
    fprintf(stderr, "%s\n", str.c_str());
#endif
}

static void
split_events(const char *events, vector<string> &splited_events)
{
    char *ptr;
    char *colon;

    ptr = strdup(events);

    while (1) {
	colon = strchr(ptr, ':');
	if (colon == NULL) {
	    splited_events.push_back(string(ptr));
	    break;
	} else {
	    *colon = '\0';
	    splited_events.push_back(string(ptr));
	    ptr = colon + 1;
	}
    }
}

static void
merge_parts(vector<string> *dst, vector<string> *src)
{
    size_t i;
    size_t dstSize;
    size_t srcSize;

    if (src == NULL) {
	return;
    }

    dstSize = dst->size();
    srcSize = src->size();

    for (i=0; i<srcSize; i++) {
	if (i < dstSize) {
	    dst->at(i) += ":";
	    dst->at(i) += src->at(i);
	} else {
	    dst->push_back(src->at(i));
	}
    }
}

/********************* CUDA Counter Partitioner *******************/
#ifdef WITH_CUPTI

typedef struct {
    CUdevice device;
    string   deviceName;

    CUpti_EventDomainID domainID;
    string              domainName;

    CUpti_EventID eventID;
    string        eventName;
} event_t;

// all available events
static vector<event_t> cuda_avail_events;

static int
cuda_get_avail_events(vector<event_t> &events)
{
    int i;
    unsigned int j, k;
    size_t size;

    int numDevices;
    CUdevice device;

    uint32_t numDomains;
    CUpti_EventDomainID *domainID;

    uint32_t numEvents;
    CUpti_EventID *eventID;

    cuDeviceGetCount(&numDevices);

    // iterate over all devices
    for (i=0; i<numDevices; i++) {
	char *ptr;
	char deviceName[64];

	cuDeviceGet(&device, i);
	cuDeviceGetName(deviceName, sizeof(deviceName), device);

	// convert space to underscore
	while ((ptr = strchr(deviceName, ' ')) != NULL) {
	    *ptr = '_';
	}

	cuptiDeviceGetNumEventDomains(device, &numDomains);

	size     = sizeof(CUpti_EventDomainID) * numDomains;
	domainID = (CUpti_EventDomainID*)malloc(size);

	cuptiDeviceEnumEventDomains(device, &size, domainID);

	// iterate over all domains
	for (j=0; j<numDomains; j++) {
	    char domainName[64];

	    size = sizeof(domainName);
	    cuptiDeviceGetEventDomainAttribute(device, domainID[j],
					       CUPTI_EVENT_DOMAIN_ATTR_NAME,
					       &size, domainName);

	    cuptiEventDomainGetNumEvents(domainID[j], &numEvents);

	    size    = sizeof(CUpti_EventID) * numEvents;
	    eventID = (CUpti_EventID*)malloc(size);

	    cuptiEventDomainEnumEvents(domainID[j], &size, eventID);

	    // iterate over all events
	    for (k=0; k<numEvents; k++) {
		char eventName[64];
		event_t event;

		size = sizeof(eventName);
		cuptiEventGetAttribute(eventID[k],
				       CUPTI_EVENT_ATTR_NAME,
				       &size, eventName);

		event.device     = device;
		event.deviceName = deviceName;

		event.domainID   = domainID[j];
		event.domainName = domainName;

		event.eventID    = eventID[k];
		event.eventName  = eventName;

		events.push_back(event);
	    }

	    free(eventID);
	}

	free(domainID);
    }

    return 0;
}

// Event should be in the form of "CUDA.<Device>.<Domain>.<Event>"
// See also "tau_cupti_avail"
static int
cuda_get_event_index(const char *event)
{
    int i = -1;
    char *cuda;
    char *deviceName;
    char *domainName;
    char *eventName;
    char *spec = strdup(event);

    cuda = spec;

    deviceName = strchr(cuda, '.');
    if (deviceName == NULL) {
	goto bail;
    } else {
	*deviceName = '\0';
	deviceName++;
    }

    domainName = strchr(deviceName, '.');
    if (domainName == NULL) {
	goto bail;
    } else {
	*domainName = '\0';
	domainName++;
    }

    eventName = strchr(domainName, '.');
    if (eventName == NULL) {
	goto bail;
    } else {
	*eventName = '\0';
	eventName++;
    }

    if (strcmp(cuda, "CUDA") != 0) {
	goto bail;
    }

    for (i=0; i<(int)cuda_avail_events.size(); i++) {
	if ((cuda_avail_events[i].deviceName == deviceName) &&
	    (cuda_avail_events[i].domainName == domainName) &&
	    (cuda_avail_events[i].eventName  == eventName)) {
	    free(spec);
	    return i;
	}
    }

    i = -1;

bail:
    free(spec);
    return i;
}

// add the event into a specific group based on device it belongs to
static int
cuda_add_event(vector< vector<int> > &groups, const char *event)
{
    unsigned int i;
    int idx;

    idx = cuda_get_event_index(event);
    if (idx < 0) {
	printf("Error: %s: no such event\n", event);
	return -1;
    }

    // iterate over exist groups to find one that fits
    for (i=0; i<groups.size(); i++) {
	if (cuda_avail_events[idx].device == cuda_avail_events[groups[i][0]].device) {
	    groups[i].push_back(idx);
	    return 0;
	}
    }

    // no fits, creat a new group
    groups.push_back(vector<int>(1, idx));
    return 0;
}

static int
set2parts(CUdevice device, CUpti_EventGroupSet *set, vector<string> *parts)
{
    string   events;
    size_t   size;
    uint32_t numEvents;
    unsigned int i, j;

    CUpti_EventID *eventID;
    CUpti_EventDomainID domainID;
    CUpti_EventGroup eventGroup;

    char *ptr;
    char deviceName[64];
    char domainName[64];
    char eventName[64];

    size = sizeof(deviceName);
    cuDeviceGetName(deviceName, size, device);

    // convert space to underscore
    while ((ptr = strchr(deviceName, ' ')) != NULL) {
	*ptr = '_';
    }

    for (i=0; i<set->numEventGroups; i++) {
	eventGroup = set->eventGroups[i];

	size = sizeof(domainID);
	cuptiEventGroupGetAttribute(eventGroup,
				    CUPTI_EVENT_GROUP_ATTR_EVENT_DOMAIN_ID,
				    &size, &domainID);

	size = sizeof(domainName);
	cuptiDeviceGetEventDomainAttribute(device, domainID,
					   CUPTI_EVENT_DOMAIN_ATTR_NAME,
					   &size, domainName);

	size = sizeof(numEvents);
	cuptiEventGroupGetAttribute(eventGroup,
				    CUPTI_EVENT_GROUP_ATTR_NUM_EVENTS,
				    &size, &numEvents);

	size    = sizeof(CUpti_EventID) * numEvents;
	eventID = (CUpti_EventID*)malloc(size);

	cuptiEventGroupGetAttribute(eventGroup,
				    CUPTI_EVENT_GROUP_ATTR_EVENTS,
				    &size, eventID);

	// it seems TAU can only measure cupti events in the same
	// domain in each pass
	events = "";
	for (j=0; j<numEvents; j++) {
	    size = sizeof(eventName);
	    cuptiEventGetAttribute(eventID[j],
				   CUPTI_EVENT_ATTR_NAME,
				   &size, eventName);

	    events += "CUDA.";
	    events += deviceName;
	    events += ".";
	    events += domainName;
	    events += ".";
	    events += eventName;
	    events += ":";
	}
	events.erase(events.length() - 1);

	parts->push_back(events);

	free(eventID);
    }

    return 0;
}

static vector<string>*
cuda_partition_groups(vector< vector<int> > &groups)
{
    unsigned int i, j;

    vector<string> *parts;

    parts = new vector<string>;

    // partition events on each device separately
    for (i=0; i<groups.size(); i++) {
	int size;
	CUpti_EventID *idArray;
	CUdevice device;
	CUcontext ctx;
	CUpti_EventGroupSets *passes;

	// put all eventID in the group into an array
	size = sizeof(CUpti_EventID) * groups[i].size();
	idArray = (CUpti_EventID*)malloc(size);
	for (j=0; j<groups[i].size(); j++) {
	    idArray[j] = cuda_avail_events[groups[i][j]].eventID;
	}

	// partition the events in the array
	device = cuda_avail_events[groups[i][0]].device;
	cuCtxCreate(&ctx, 0, device);
	cuptiEventGroupSetsCreate(ctx, size, idArray, &passes);
	cuCtxDestroy(ctx);

	for (j=0; j<passes->numSets; j++) {
	    set2parts(device, passes->sets+j, parts);
	}
    }

    return parts;
}

static vector<string>*
cuda_partitioner(const char *dbfile, vector<string> &events,
		 char *algo="greedy", bool fashion=false)
{
    // events grouped by device
    vector< vector<int> > groups;

    vector<string>::iterator iter;

    if (events.size() == 0) {
	return NULL;
    }

    for (iter=events.begin(); iter!=events.end(); iter++) {
	cuda_add_event(groups, iter->c_str());
    }

    return cuda_partition_groups(groups);
}

#endif // WITH_CUPTI

/********************* PAPI Counter Partitioner ******************/

#define GREEDY_RETRY 100
#define MAX_LEN_62   128	// max length of 62 based number we
				// are going to use

extern int _papi_hwi_errno;

#define PAPI_STRERROR() (PAPI_strerror(_papi_hwi_errno))

static sqlite3 *db;
static vector<PAPI_event_info_t> papi_avail_counters;

static int
my_rand(int i)
{
    return rand() % i;
}

// static const char *
// is_derived( PAPI_event_info_t &info )
// {
//     if (strlen(info.derived ) == 0) 
// 	return "No";
//     else if (strcmp(info.derived, "NOT_DERIVED") == 0) 
// 	return "No";
//     else if (strcmp(info.derived, "DERIVED_CMPD") == 0) 
// 	return "No";
//     else
// 	return "Yes";
// }

// static int
// _dump_counter(PAPI_event_info_t &info)
// {
//     printf("%-13s%#x  %-5s%s", info.symbol,
// 	   info.event_code, is_derived(info), info.long_descr);
//     if (info.note[0]) {
// 	printf(" (%s)", info.note);
//     }
//     printf("\n");

//     return 0;
// }

// static int
// dump_counters(vector<PAPI_event_info_t> &counters)
// {
//     vector<PAPI_event_info_t>::iterator iter;

//     for (iter=counters.begin(); iter!=counters.end(); iter++) {
// 	_dump_counter(*iter);
//     }

//     return 0;
// }

static int
papi_get_avail_counters(vector<PAPI_event_info_t> &counters)
{
    int rv;
    int event_code;
    PAPI_event_info_t info;

    event_code = 0 | PAPI_PRESET_MASK;

    rv = PAPI_enum_event(&event_code, PAPI_ENUM_FIRST);
    if (rv != PAPI_OK) {
	report_error("PAPI_enum_event", PAPI_STRERROR(), XSTR(__LINE__));
	return rv;
    }

    do {
	rv = PAPI_get_event_info(event_code, &info);
	if (rv != PAPI_OK) {
	    report_error("PAPI_get_event_info", PAPI_STRERROR(), XSTR(__LINE__));
	    return rv;
	}

	if (info.count != 0) {
	    counters.push_back(info);
	}
    } while (PAPI_enum_event(&event_code, PAPI_PRESET_ENUM_AVAIL) == PAPI_OK);

    return 0;
}

static vector<string>*
_papi_greedy_partition(vector<string> &events)
{
    int rv;
    vector<int> event_sets;
    vector<string> *parts = new vector<string>;

    unsigned int i, j;

    for (i=0; i<events.size(); i++) {
	for (j=0; j<event_sets.size(); j++) {
	    rv = PAPI_add_named_event(event_sets[j], (char*)events[i].c_str());
	    if (rv == PAPI_OK) {
		parts->at(j) += ":" + events[i];
		break;
	    } else {
		/* can not put in this event_set, try next one */
		continue;
	    }
	}

	/*
	 * none of existing event_set could hold this counter, let's
	 * create a new set
	 */
	if (j == event_sets.size()) {
	    int set = PAPI_NULL;

	    rv = PAPI_create_eventset(&set);
	    if (rv != PAPI_OK) {
		report_error("PAPI_create_eventset", PAPI_STRERROR(), XSTR(__LINE__));
		goto bail;
	    }

	    rv = PAPI_add_named_event(set, (char*)events[i].c_str());
	    if (rv == PAPI_OK) {
		event_sets.push_back(set);
		parts->push_back(events[i]);
	    } else {
		/* this should not happen */
		report_error("PAPI_add_event", PAPI_STRERROR(), XSTR(__LINE__));
		goto bail;
	    }
	}
    }

    /* release event sets */
    for (i=0; i<event_sets.size(); i++) {
	rv = PAPI_cleanup_eventset(event_sets[i]);
	if (rv != PAPI_OK) {
	    report_error("PAPI_cleanup_eventset", PAPI_STRERROR(), XSTR(__LINE__));
	    goto bail;
	}

	rv =PAPI_destroy_eventset(&event_sets[i]);
	if (rv != PAPI_OK) {
	    report_error("PAPI_destroy_eventset", PAPI_STRERROR(), XSTR(__LINE__));
	    goto bail;
	}
    }

    return parts;

bail:
    delete parts;
    return NULL;
}

static vector<string>*
papi_greedy_partition(vector<string> &events)
{
    int i;
    unsigned int nparts = events.size() + 1;
    vector<string> *parts = NULL;

    // try greedy with random order for several times
    for (i=0; i<GREEDY_RETRY; i++) {
	vector <string> *_parts;
	random_shuffle(events.begin(), events.end(), my_rand);

	_parts = _papi_greedy_partition(events);
	if (_parts == NULL) {
	    delete parts;
	    return NULL;
	}
	
	if (_parts->size() < nparts) {
	    /* get a better result */
	    delete parts;
	    parts  = _parts;
	    nparts = parts->size();
	} else {
	    /* drop the result */
	    delete _parts;
	}
    }

    return parts;
}

static int
_get_one_part(void *data, int ncol, char **text, char **name)
{
    vector<string> *parts;

    parts = (vector<string>*) data;

    parts->push_back(text[0]);

    return 0;
}

static vector<string>*
papi_cached_partition(vector<string> &events)
{
    string sql;
    vector<string> *parts;
    char *err;

    stringstream ss;
    ostream_iterator<string> ssit(ss, ":");
    sort(events.begin(), events.end());
    copy(events.begin(), events.end(), ssit);

    sql += "SELECT part from partition WHERE events='";
    sql += ss.str();
    sql += "';";

    parts  = new vector<string>;
    sqlite3_exec(db, sql.c_str(), _get_one_part, parts, &err);
    if (err != NULL) {
	report_error("SQLite3", err, XSTR(__LINE__));
	sqlite3_free(err);
	delete parts;
	return NULL;
    }

    return parts;
}

static int
_papi_save_result(string &key, string &part)
{
    char *err;
    string sql;
    vector<int>::iterator iter;

    sql += "INSERT INTO partition (events, part) VALUES ('";
    sql += key;
    sql += "', '";
    sql += part;
    sql += "');";

    sqlite3_exec(db, sql.c_str(), NULL, NULL, &err);
    if (err != NULL) {
	fprintf(stderr, "SQLite: %s\n", err);
	sqlite3_free(err);
	return -1;
    }

    return 0;
}

static int
papi_save_result(string &key, vector<string> *parts)
{
    vector<string>::iterator iter;

    for (iter=parts->begin(); iter!=parts->end(); iter++) {
	_papi_save_result(key, *iter);
    }

    return 0;
}

static int
papi_delete_result(string &key)
{
    char *err;
    string sql;

    sql += "DELETE FROM partition WHERE events='";
    sql += key;
    sql += "';";

    sqlite3_exec(db, sql.c_str(), NULL, NULL, &err);
    if (err != NULL) {
	fprintf(stderr, "SQLite: %s\n", err);
	sqlite3_free(err);
	return -1;
    }

    return 0;
}

static int
papi_update_result(vector<string> &events, vector<string> *parts)
{
    int rv;

    stringstream ss;
    ostream_iterator<string> ssit(ss, ":");
    sort(events.begin(), events.end());
    copy(events.begin(), events.end(), ssit);

    string key = ss.str();

    rv = papi_delete_result(key);
    if (rv != 0) {
	goto bail;
    }

    rv = papi_save_result(key, parts);
    if (rv != 0) {
	goto bail;
    }

bail:
    return rv;
}

static int
papi_setup_schema(void)
{
    char *err;
    char *schema =
	"CREATE TABLE IF NOT EXISTS partition (\n"
	"       id INTEGER PRIMARY KEY,\n"
	"       events TEXT,\n"
	"       part TEXT\n"
	");";

    sqlite3_exec(db, schema, NULL, NULL, &err);
    if (err != NULL) {
	report_error("SQLite3", err, XSTR(__LINE__));
	sqlite3_free(err);
	return -1;
    }

    return 0;
}

typedef vector<string>* (*papi_partitioner_t)(vector<string> &events);

static vector<string>*
papi_partitioner(const char *dbfile, vector<string> &events,
		 char *algo="greedy", bool fashion=false)
{
    int rv;
    unsigned int i;
    vector<string>* parts = NULL;
    vector<string>* cached_parts;

    vector<string>::iterator iter;

    /* partitioner algo table */
    struct {
	char *name;
	papi_partitioner_t partition;
    } algos[] = {
	{"cached", papi_cached_partition},
	{"greedy", papi_greedy_partition},
    };

    /* check whether requested events are avaiable for current platform */
    for(iter=events.begin(); iter!=events.end(); iter++) {
	for (i=0; i<papi_avail_counters.size(); i++) {
	    if (*iter == papi_avail_counters[i].symbol) {
		break;
	    }
	}

	if (i == papi_avail_counters.size()) {
	    report_error("Event doesn't exist", iter->c_str(), XSTR(__LINE__));
	    return NULL;
	}
    }

    /* SQLite3 setup */
    rv = sqlite3_open(dbfile, &db);
    if (rv != 0) {
	report_error("SQLite3", sqlite3_errmsg(db), XSTR(__LINE__));
	goto bail;
    }

    rv = papi_setup_schema();
    if (rv != 0) {
	goto bail;
    }

    /* partition PAPI events using the given algo */
    for (i=0; i<sizeof(algos)/sizeof(algos[0]); i++) {
	if (strcasecmp(algo, algos[i].name) == 0) {
	    parts = algos[i].partition(events);
	    break;
	}
    }

    if (i == sizeof(algos)/sizeof(algos[0])) {
	report_error("No such partition algo", algo, XSTR(__LINE__));
	goto bail;
    }

    // something wrong in partition process
    if (parts == NULL) {
	goto bail;
    }

    cached_parts = papi_cached_partition(events);
    if (cached_parts == NULL) {
	delete parts;
	parts = NULL;
	goto bail;
    }

    if ((cached_parts->size() == 0) ||
	(parts->size() < cached_parts->size())) {
	papi_update_result(events, parts);
    }

    if (fashion) {
	/* use the latest partition result */
    } else {
	/* use the best partition result */
	if ((cached_parts->size() == 0) ||
	    (parts->size() < cached_parts->size())) {
	    delete cached_parts;
	} else {
	    delete parts;
	    parts = cached_parts;
	}
    }

bail:
    /* clean up */
    sqlite3_close(db);

    return parts;
}


static vector<string>*
misc_partitioner(const char *dbfile, vector<string> &events,
		 char *algo="greedy", bool fashion=false)
{
    size_t i;
    string part;
    vector<string> *parts;

    if (events.size() == 0) {
	return NULL;
    }

    for (i=0; i<events.size(); i++) {
	part += events[i];
	part += ':';
    }

    part.erase(part.length() - 1);

    parts = new vector<string>;
    parts->push_back(part);

    return parts;
}

static vector<string>*
partitioner(const char *dbfile, vector<string> &events,
	    char *algo="greedy", bool fashion=false)
{
    size_t i;
    vector<string> *parts, *_parts;
    vector<string> papi_events;
#if WITH_CUPTI
    vector<string> cuda_events;
#endif // WITH_CUPTI
    vector<string> misc_events;
    vector<string>::iterator iter;

    parts = new vector<string>;

    for (i=0; i<events.size(); i++) {
	if (events[i].compare(0, 5, "PAPI_") == 0) {
	    papi_events.push_back(events[i]);
	}
#if WITH_CUPTI
	else if (events[i].compare(0, 5, "CUDA.") == 0) {
	    cuda_events.push_back(events[i]);
	}
#endif // WITH_CUPTI
	else {
	    misc_events.push_back(events[i]);
	}
    }

    _parts = papi_partitioner(dbfile, papi_events, algo, fashion);
    merge_parts(parts, _parts);
    delete _parts;

#if WITH_CUPTI
    _parts = cuda_partitioner(dbfile, cuda_events, algo, fashion);
    merge_parts(parts, _parts);
    delete _parts;
#endif // WITH_CUPTI

    _parts = misc_partitioner(dbfile, misc_events, algo, fashion);
    merge_parts(parts, _parts);
    delete _parts;

    return parts;
}

#ifndef EXT_PYTHON

int
main(int argc, char **argv)
{
    int  rv;
    unsigned int i;
    char *dbfile; 
    vector<string> events;
    char *algo   = "greedy";
    bool fashion = false;

    vector<string> *parts;

    if ((argc < 3) || (argc > 5)) {
	printf("Usage: "
	       "partitioner <sqlite3.db> "
	       "<EVENT1>[:EVENT2][:EVENT3]... [greedy|cached] "
	       "[true|false|0|1]\n");
	return 0;
    }

    dbfile = argv[1];

    split_events(argv[2], events);

    if (argc >= 4) {
	algo = argv[3];
    }

    if (argc >= 5) {
	if ((strcasecmp(argv[4], "false") == 0) ||
	    (strcasecmp(argv[4], "0")    == 0)) {
	    fashion = false;
	} else {
	    fashion = true;
	}
    }

    srand(time(0));

    /* PAPI init */
    rv = PAPI_library_init(PAPI_VER_CURRENT);
    if (rv != PAPI_VER_CURRENT) {
	// printf("PAPI_VER_CURRENT = %x\n", PAPI_VER_CURRENT);
	report_error("PAPI_library_init", PAPI_STRERROR(), XSTR(__LINE__));
	return -1;
    }

    papi_get_avail_counters(papi_avail_counters);

#ifdef WITH_CUPTI
    /* CUDA init */
    cuInit(0);
    cuda_get_avail_events(cuda_avail_events);
#endif // WITH_CUPTI

    parts = partitioner(dbfile, events, algo, fashion);

    if (parts != NULL) {
	for (i=0; i<parts->size(); i++) {
	    printf("%2d: %s\n", i, parts->at(i).c_str());
	}
	delete parts;
    }

    return 0;
}

#else

/********** Python Extension **************/

/*
 * Args:
 *   dbfile  (string)     : cache database filename
 *   events  (string)     : colon separated event names
 *           (string list): list of event names
 *   algo    (string)     : partition algorithm
 *   fashion (bool)       : ignore cached results or not
 */
static PyObject*
py_partitioner(PyObject *self, PyObject *args)
{
    int i;
    int rv;

    PyObject *list;

    char *dbfile;
    PyObject *_events;
    char *algo = "greedy";
    PyObject *_fashion = Py_False;

    vector<string> events;
    bool fashion;

    int nparts;
    vector<string> *parts;

    string builtins, papi;

    rv = PyArg_ParseTuple(args, "sO|sO",
			  &dbfile, &_events, &algo, &_fashion);
    if (!rv) {
	return NULL;
    }

    if (PyList_Check(_events)) {
	PyObject *iter;
	PyObject *_event;

	if (PyList_GET_SIZE(_events) == 0) {
	    return PyList_New(0);
	}

	iter = PyObject_GetIter(_events);
	if (iter == NULL) {
	    return NULL;
	}

	/* extract event strings */
	while (1) {
	    _event = PyIter_Next(iter);
	    if (_event == NULL) {
		break;
	    }

	    //if (!PyString_Check(_event)) {
	    const char* event_name = PyBytes_AsString(_event);
	    if (!event_name) {
		PyErr_SetString(PyExc_TypeError, "String or String List needed");
		return NULL;
	    }

	    events.push_back(event_name);
	}
    } else if (PyBytes_AsString(_events)) {
	split_events(PyBytes_AsString(_events), events);
    } else {
	PyErr_SetString(PyExc_TypeError, "String or String List needed");
	return NULL;
    }

    if (PyObject_IsTrue(_fashion)) {
        fashion = true;
    } else {
        fashion = false;
    }

    parts = partitioner(dbfile, events, algo, fashion);
    if (parts == NULL) {
	return NULL;
    }

    nparts = parts->size();
    list  = PyList_New(nparts);

    for (i=0; i<nparts; i++) {
	PyList_SetItem(list, i, PyUnicode_FromString(parts->at(i).c_str()));
    }

    delete parts;

    return list;
}

static PyMethodDef PartMethods[] = {
    {
	"partitioner",
	(PyCFunction) py_partitioner,
	METH_VARARGS,
	"Partitions the given events to minimize number of runs required.",
    },

    {NULL, NULL, 0, NULL}
};


PyMODINIT_FUNC
PyInit_partitioner(void)
{
    PyObject *m;

    srand(time(0));

    /* PAPI init */
    PAPI_library_init(PAPI_VER_CURRENT);
    papi_get_avail_counters(papi_avail_counters);

#ifdef WITH_CUPTI
    /* CUDA init */
    cuInit(0);
    cuda_get_avail_events(cuda_avail_events);
#endif // WITH_CUPTI

    //m = Py_InitModule("partitioner", PartMethods);

    static struct PyModuleDef PartModule =
    {
        PyModuleDef_HEAD_INIT,
        "partitioner", /* name of module */
        "",          /* module documentation, may be NULL */
        -1,          /* size of per-interpreter state of the module, or -1 if the module keeps state in global variables. */
        PartMethods
    };
    m = PyModule_Create( &PartModule );
    if (m == NULL) {
	return m;
    }

    PartError = PyErr_NewException("partitioner.error", NULL, NULL);
    Py_INCREF(PartError);
    PyModule_AddObject(m, "error", PartError);
    return m;
}

#endif
