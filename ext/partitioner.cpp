#ifdef EXT_PYTHON
#include <Python.h>
#endif

#include <stdio.h>
#include <string.h>
#include <stdlib.h>
#include <strings.h>

#include <new>
#include <vector>
#include <iostream>
#include <algorithm>

#include <papi.h>
#include <gmp.h>
#include <sqlite3.h>

using namespace std;

#define  XSTR(s) _XSTR(s)
#define _XSTR(s) #s

#define GREEDY_RETRY 100
#define MAX_LEN_62   128	// max length of 62 based number we
				// are going to use

extern int _papi_hwi_errno;

#define PAPI_STRERROR() (PAPI_strerror(_papi_hwi_errno))

static sqlite3 *db;
static vector<PAPI_event_info_t> avail_counters;

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

static string
chooser2string(mpz_t chooser)
{
    string str;
    mp_bitcnt_t start = 0, found;

    if (mpz_cmp_ui(chooser, 0) == 0) {
	return "";
    }

    while (1) {
	found = mpz_scan1(chooser, start);

	if (found == ULONG_MAX) {
	    break;
	}

	start = found + 1;

	str += avail_counters[found].symbol;
	str += ":";
    }

    str.erase(str.length() - 1);

    return str;
}

static string
chooser2string(vector<mp_bitcnt_t> &chooser)
{
    mpz_t c;
    vector<mp_bitcnt_t>::iterator iter;

    mpz_init_set_ui(c, 0);

    for (iter=chooser.begin(); iter!=chooser.end(); iter++) {
	mpz_setbit(c, *iter);
    }

    string str = chooser2string(c);

    mpz_clear(c);

    return str;
}

static string
chooser2string(char *chooser)
{
    mpz_t c;
    mpz_init_set_str(c, chooser, 62);

    string str = chooser2string(c);

    mpz_clear(c);

    return str;
}

static int
string2chooser(const char *str, mpz_t chooser)
{
    unsigned int i;
    int len;
    const char *ptr;
    char *name;
    bool done = false;

    mpz_set_ui(chooser, 0);

    while (!done) {
	ptr = strchr(str, ':');

	if (ptr == NULL) {
	    len = strlen(str);
	    done = true;
	} else {
	    len = ptr - str;
	}

	for (i=0; i<avail_counters.size(); i++) {
	    name = avail_counters[i].symbol;
	    if (strncmp(name, str, len) == 0) {
		mpz_setbit(chooser, i);
		break;
	    }
	}

	if (i == avail_counters.size()) {
	    report_error("Counter doesn't exist", str, XSTR(__LINE__));
	    return -1;
	} else {
	    str = ptr + 1;
	}
    }

    return 0;
}

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
get_avail_counters(vector<PAPI_event_info_t> &counters)
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

static void
free_parts(vector<char*> *parts)
{
    vector<char*>::iterator iter;

    if (parts == NULL) {
	return;
    }

    for (iter=parts->begin(); iter!=parts->end(); iter++) {
	free(*iter);
    }

    delete parts;
}

#ifndef EXT_PYTHON
static void
dump_parts(vector<char*> *parts)
{
    unsigned int i;

    for (i=0; i<parts->size(); i++) {
	printf("%2d: %s\n", i+1, chooser2string((*parts)[i]).c_str());
    }
}
#endif

static vector<char*>*
_greedy_partition(vector<mp_bitcnt_t> &group)
{
    int rv;
    vector<int> event_sets;
    vector< vector<mp_bitcnt_t> > parts; // parts in index-vector
					 // representation

    unsigned int i, j;

    for (i=0; i<group.size(); i++) {
	mp_bitcnt_t index = group[i];
	int event_code    = avail_counters[index].event_code;

	for (j=0; j<event_sets.size(); j++) {
	    rv = PAPI_add_event(event_sets[j], event_code);
	    if (rv == PAPI_OK) {
		parts[j].push_back(index);
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
		exit(1);
	    }

	    rv = PAPI_add_event(set, event_code);
	    if (rv == PAPI_OK) {
		event_sets.push_back(set);
		parts.push_back(vector<mp_bitcnt_t>(1, index));
	    } else {
		/* this should not happen */
		report_error("PAPI_add_event", PAPI_STRERROR(), XSTR(__LINE__));
		printf("i=%d, j=%d\n", i, j);
		printf("events: %s\n", chooser2string(group).c_str());
		exit(1);
	    }
	}
    }

    /* release event sets */
    for (i=0; i<event_sets.size(); i++) {
	rv = PAPI_cleanup_eventset(event_sets[i]);
	if (rv != PAPI_OK) {
	    report_error("PAPI_cleanup_eventset", PAPI_STRERROR(), XSTR(__LINE__));
	    exit(1);
	}

	rv =PAPI_destroy_eventset(&event_sets[i]);
	if (rv != PAPI_OK) {
	    report_error("PAPI_destroy_eventset", PAPI_STRERROR(), XSTR(__LINE__));
	    exit(1);
	}
    }

    mpz_t x;
    vector<char*> *bf_parts;	// parts in bit-field representation
    vector<mp_bitcnt_t>::iterator pbit;
    vector< vector<mp_bitcnt_t> >::iterator ppart;

    mpz_init(x);
    bf_parts = new vector<char*>;

    for (ppart=parts.begin(); ppart!=parts.end(); ppart++) {
	mpz_set_ui(x, 0);

	for (pbit=ppart->begin(); pbit!=ppart->end(); pbit++) {
	    mpz_setbit(x, *pbit);
	}

	bf_parts->push_back(mpz_get_str(NULL, 62, x));
    }

    mpz_clear(x);

    return bf_parts;
}

static vector<char*>*
greedy_partition(mpz_t chooser)
{
    vector<mp_bitcnt_t> group;
    mp_bitcnt_t start = 0, found;

    while (1) {
	found = mpz_scan1(chooser, start);

	if (found == ULONG_MAX) {
	    break;
	}

	start = found + 1;
	group.push_back(found);
    }

    int i;
    unsigned int nparts = group.size() + 1;
    vector<char*> *parts = NULL;

    // try greedy with random order for several times
    for (i=0; i<GREEDY_RETRY; i++) {
	vector <char*> *_parts;
	random_shuffle(group.begin(), group.end(), my_rand);

	_parts = _greedy_partition(group);
	if (_parts->size() < nparts) {
	    /* get a better result */
	    free_parts(parts);
	    parts  = _parts;
	    nparts = parts->size();
	} else {
	    /* drop the result */
	    free_parts(_parts);
	}
    }

    return parts;
}

static int
get_one_part(void *data, int ncol, char **text, char **name)
{
    vector<char*> *parts;

    parts = (vector<char*>*) data;

    parts->push_back(strdup(text[0]));

    return 0;
}

static vector<char*>*
cached_partition(mpz_t chooser)
{
    string sql;
    vector<char*> *parts;
    char *events;
    char *err;

    parts  = new vector<char*>;
    events = mpz_get_str(NULL, 62, chooser);

    sql += "SELECT part from partition WHERE events='";
    sql += events;
    sql += "';";

    free(events);

    sqlite3_exec(db, sql.c_str(), get_one_part, parts, &err);
    if (err != NULL) {
	report_error("SQLite3", err, XSTR(__LINE__));
	sqlite3_free(err);
	delete parts;
	return NULL;
    }

    return parts;
}

static int
_save_result(char *events, char *part)
{
    char *err;
    string sql;
    vector<int>::iterator iter;

    sql += "INSERT INTO partition (events, part) VALUES ('";
    sql += events;
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
save_result(char *events, vector<char*> *parts)
{
    vector<char*>::iterator iter;

    for (iter=parts->begin(); iter!=parts->end(); iter++) {
	_save_result(events, *iter);
    }

    return 0;
}

static int
delete_result(char *chooser)
{
    char *err;
    string sql;

    sql += "DELETE FROM partition WHERE events='";
    sql += chooser;
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
update_result(mpz_t chooser, vector<char*> *parts)
{
    int rv;
    char *events;

    events = mpz_get_str(NULL, 62, chooser);

    rv = delete_result(events);
    if (rv != 0) {
	goto bail;
    }

    rv = save_result(events, parts);
    if (rv != 0) {
	goto bail;
    }

bail:
    free(events);
    return rv;
}

static int
setup_schema(void)
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

typedef vector<char*>* (*partitioner_t)(mpz_t);

static vector<char*>*
partitioner(const char *dbfile, const char *events,
	    char *algo="greedy", bool fashion=false)
{
    int rv;
    unsigned int i;
    mpz_t chooser;
    vector<char*>* parts = NULL;
    vector<char*>* cached_parts;

    /* partitioner algo table */
    struct {
	char *name;
	partitioner_t partition;
    } algos[] = {
	{"cached", cached_partition},
	{"greedy", greedy_partition},
    };

    mpz_init(chooser);

    /* SQLite3 setup */
    rv = sqlite3_open(dbfile, &db);
    if (rv != 0) {
	report_error("SQLite3", sqlite3_errmsg(db), XSTR(__LINE__));
	goto bail;
    }

    rv = setup_schema();
    if (rv != 0) {
	goto bail;
    }

    rv = string2chooser(events, chooser);
    if (rv < 0) {
	goto bail;
    }

    /* partition the events using the given algo */
    for (i=0; i<sizeof(algos)/sizeof(algos[0]); i++) {
	if (strcasecmp(algo, algos[i].name) == 0) {
	    parts = algos[i].partition(chooser);
	    break;
	}
    }

    if (i == sizeof(algos)/sizeof(algos[0])) {
	report_error("No such partition algo", algo, XSTR(__LINE__));
	goto bail;
    }

    cached_parts = cached_partition(chooser);
    if (cached_parts == NULL) {
	free_parts(parts);
	goto bail;
    }

    if ((cached_parts->size() == 0) ||
	(parts->size() < cached_parts->size())) {
	update_result(chooser, parts);
    }

    if (fashion) {
	/* use the latest partition result */
    } else {
	/* use the best partition result */
	if ((cached_parts->size() == 0) ||
	    (parts->size() < cached_parts->size())) {
	    free_parts(cached_parts);
	} else {
	    free_parts(parts);
	    parts = cached_parts;
	}
    }

bail:
    /* clean up */
    mpz_clear(chooser);
    sqlite3_close(db);

    return parts;
}

#ifndef EXT_PYTHON

int
main(int argc, char **argv)
{
    int  rv;

    char *dbfile; 
    char *events;
    char *algo   = "greedy";
    bool fashion = false;

    vector<char*> *parts;

    if ((argc < 3) || (argc > 5)) {
	printf("Usage: "
	       "partitioner <sqlite3.db> "
	       "<EVENT1>[:EVENT2][:EVENT3]... [greedy|cached] "
	       "[true|false|0|1]\n");
	return 0;
    }

    dbfile = argv[1];
    events = argv[2];

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

    get_avail_counters(avail_counters);

    parts = partitioner(dbfile, events, algo, fashion);

    if (parts != NULL) {
	dump_parts(parts);
	free_parts(parts);
    }

    return 0;
}

#else

/********** Python Extension **************/

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

    string events;
    bool fashion;

    int nparts;
    vector<char*> *parts;

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

	    if (!PyString_Check(_event)) {
		PyErr_SetString(PyExc_TypeError, "String or String List needed");
		return NULL;
	    }

	    events += PyString_AS_STRING(_event);
	    events += ":";
	}

	events.erase(events.length() - 1);
    } else if (PyString_Check(_events)) {
	events = PyString_AS_STRING(_events);
    } else {
	PyErr_SetString(PyExc_TypeError, "String or String List needed");
	return NULL;
    }

    if (PyBool_Check(_fashion)) {
	if (_fashion == Py_True) {
	    fashion = true;
	} else {
	    fashion = false;
	}
    } else {
	PyErr_SetString(PyExc_TypeError, "Bool needed");
	return NULL;
    }

    parts = partitioner(dbfile, events.c_str(), algo, fashion);
    if (parts == NULL) {
	return NULL;
    }

    nparts = parts->size();
    list  = PyList_New(nparts);
    for (i=0; i<nparts; i++) {
	string str = chooser2string((*parts)[i]);
	PyList_SetItem(list, i, PyString_FromString(str.c_str()));
    }

    //free_parts(parts);

    return list;
}

static PyMethodDef PartMethods[] = {
    {
	"partitioner",
	py_partitioner,
	METH_VARARGS,
	"Partition the given events.",
    },
};

PyMODINIT_FUNC
initpartitioner(void)
{
    PyObject *m;

    srand(time(0));

    /* PAPI init */
    PAPI_library_init(PAPI_VER_CURRENT);
    get_avail_counters(avail_counters);

    m = Py_InitModule("partitioner", PartMethods);
    if (m == NULL) {
	return;
    }

    PartError = PyErr_NewException("partitioner.error", NULL, NULL);
    Py_INCREF(PartError);
    PyModule_AddObject(m, "error", PartError);
}

#endif
