// Namespace
var Canvas = Canvas || { };

function canvas_init() {
    _.templateSettings.variable = "data";

    Canvas.model = new Canvas.Model();

    Canvas.view  = new Canvas.View({
	model: Canvas.model
    });

    Canvas.router = new Canvas.Router();

    Backbone.history.start();

    // kick start
    Canvas.model.fetch();
};

/////////////////////
//
// Data Models/Collections: App, Trial, Metric, Thread, Metadata, Profile

Canvas.AppModel = Backbone.Model.extend({
    defaults: {
	name:   "anApp",  // name of the Application
    }
});

Canvas.AppCollection = Backbone.Collection.extend({
    model: Canvas.AppModel,

    url: "api/applications",
});

Canvas.TrialModel = Backbone.Model.extend({
    defaults: {
	id:   0,
	name: "aTrial"
    }
});

Canvas.TrialCollection = Backbone.Collection.extend({
    model: Canvas.TrialModel,

    update: function(appName) {
	this.url = "api/trials/" + appName;
	return this.fetch();
    }
});

Canvas.MetricModel = Backbone.Model.extend({
    defaults: {
	id: 0,
	name: "aMetric"
    }
});

Canvas.MetricCollection = Backbone.Collection.extend({
    model: Canvas.MetricModel,

    update: function(trialId) {
	this.url = "api/metrics/" + trialId;
	return this.fetch();
    }
});

Canvas.ThreadModel = Backbone.Model.extend({
    defaults: {
	id: 0,
	name: "aThread",
    }
});

Canvas.ThreadCollection = Backbone.Collection.extend({
    model: Canvas.ThreadModel,

    update: function(trialId) {
	this.url = "api/threads/" + trialId;
	return this.fetch();
    },

    parse: function(response) {
	var get_thread_name = function(idx) {
	    var tid_map = {
		"-1": "Mean (No Null)",
		"-2": "Total",
		"-3": "Std Dev (No Null)",
		"-4": "Min",
		"-5": "Max",
		"-6": "Mean",
		"-7": "Std Dev",
	    };

	    if (idx < 0) {
		return tid_map[idx];
	    } else {
		return idx;
	    }
	};

	return response.map(function(item) {
	    return {
		id: item.id,
		name: get_thread_name(item.thread_index)
	    };
	});
    }
});

Canvas.MetadataModel = Backbone.Model.extend({
    defaults: {
	name: "theName",
	value: "theValue",
    }
});

Canvas.MetadataCollection = Backbone.Collection.extend({
    model: Canvas.MetadataModel,

    update: function(trialId) {
	var self = this;

	this.url = "api/metadata/" + trialId;

	this.trigger("fetch");
	this.fetch().done(function() {
	    self.trigger("ready");
	});
    }
});

Canvas.ProfileModel = Backbone.Model.extend({
    defaults: {
	timer_callpath: "callpath",
	id: "id",
	short_name: "short_name",
	inclusive_value: "inclusive_value",
	inclusive_percent: "inclusive_percent",
	exclusive_value: "exclusive_value",
	exclusive_percent: "exclusive_percent",
    }
});

Canvas.ProfileCollection = Backbone.Collection.extend({
    model: Canvas.ProfileModel,

    update: function(threadId, metricId) {
	var self = this;

	this.url = "api/profile/" + threadId + "/" + metricId;

	this.trigger("fetch");
	this.fetch().done(function() {
	    self.trigger("ready");
	});
    }
});

/////////////////////
//
// Login Modal

Canvas.LoginModel = Backbone.Model.extend({
    defaults: {
	// loged in or not
	status: undefined,

	// connection parameter if loged in
	dbhost: undefined,
	dbname: undefined,
	dbuser: undefined,

	// name of the active session
	active: undefined,

	// saved session list
	sessions: { },
    },

    url: "api/logedIn",

    initialize: function() {
	// load saved sessions from local storage
	var active = JSON.parse(localStorage.getItem('active'));
	var sessions = JSON.parse(localStorage.getItem('sessions'));

	if (active) {
	    this.set('active', active);
	}

	if (sessions) {
	    this.set('sessions', sessions);
	}

	this.on("change:status", function() {
	    if (this.get("status") == "Good") {
		this.trigger("ready");
	    }
	});
    },

    save: function() {
	// write sessions to local storage
	localStorage.setItem('active', JSON.stringify(this.get('active')));
	localStorage.setItem('sessions', JSON.stringify(this.get('sessions')));
    },

    addSession: function(name, dbhost, dbname, dbuser) {
	var sessions = this.get("sessions");

	this.set("active", name);
	this.set("dbhost", dbhost);
	this.set("dbname", dbname);
	this.set("dbuser", dbuser);

	// save the session only if a name is provided
	if (name) {
	    sessions[name] = {
		dbhost: dbhost,
		dbname: dbname,
		dbuser: dbuser,
	    };

	    this.trigger("change:sessions");
	}

	this.save();

	// mark the login status as Good at the end
	this.set("status", "Good");
    },

    rmSession: function(name) {
	var sessions = this.get("sessions");

	delete sessions[name];

	this.save();
	this.trigger("change:sessions");
    },

    getSession: function(name) {
	return this.get("sessions")[name];
    },
});

Canvas.LoginView = Backbone.View.extend({
    events: {
	"submit":             "submitForm",
	"click li a":         "loadSession",
	"click button.close": "rmSession",
    },

    initialize: function(options) {
	_.bindAll(this, "submitForm", "hide", "show", "render");

	this.$el.modal({
	    backdrop: 'static',
	    keyboard: false,
	    show:     false,
	});

	this.template = _.template(
            $("script.template#session-dropdown-template").html()
        );

	this.render();

	this.listenTo(this.model, "change:sessions", this.render);
	this.listenTo(this.model, "change:status", this.toggle);
    },

    loadSession: function(evt) {
	var name = $(evt.currentTarget).children("span").text();
	var session = this.model.getSession(name);

	$('input[name=name]').val(name);
	$('input[name=dbhost]').val(session.dbhost);
	$('input[name=dbname]').val(session.dbname);
	$('input[name=dbuser]').val(session.dbuser);
	$('input[name=dbpass]').focus();
    },

    rmSession: function(evt) {
	var name = $(evt.currentTarget).next().text();
	this.model.rmSession(name);
	event.stopPropagation();
    },

    render: function() {
	var list = $(".dropdown-menu", this.$el);
	var sessions = this.model.get("sessions");

	list.html(this.template(sessions));

	if (Object.keys(sessions).length == 0) {
	    $("#session-picker", this.$el).parent().removeClass('open');
	    $("#session-picker", this.$el).prop("disabled",true);
	}
    },

    toggle: function(model, value) {
	if (value == "Good") {
	    this.hide();
	} else {
	    this.show();
	}
    },

    hide: function() {
	this.$el.modal('hide');
    },

    show: function() {
	$('input[name=dbpass]', this.$el).focus();
	$('input[name=dbpass]', this.$el).val("");
	$("#info", this.$el).attr("class", "").html("");
	this.$el.modal('show');
    },

    submitForm: function(event) {
	var self =  this;
	var formData = {
	    dbhost: $('input[name=dbhost]', this.$el).val(),
	    dbname: $('input[name=dbname]', this.$el).val(),
	    dbuser: $('input[name=dbuser]', this.$el).val(),
	    dbpass: $('input[name=dbpass]', this.$el).val()
	};

	$.post("api/login", formData, function(data) {
	    if (data.status == "Succeed") {
		var name = $('input[name=name]', this.$el).val();

		self.model.addSession(
		    name,
		    formData['dbhost'],
		    formData['dbname'],
		    formData['dbuser']
		);
	    } else {
		$("#info", this.$el).attr("class", "alert alert-danger")
		    .html("Cannot connect to TAUdb with specified parameters.");
	    }
	});

	// stop the form from submitting the normal way and refreshing the page
	event.preventDefault();
    }
});

/////////////////////
//
// Data Source Modal

// Generated External Events:
//  - ready          Data Source parameter are valid and ready to use
//  - ready:apps     apps list is grabed, view can use it to render content
//  - ready:trials   trials list is grabed, view can use it to render content
//  - ready:metrics  metrics list is grabed, view can use it to render content
//  - ready:threads  threads list is grabed, view can use it to render content
Canvas.DSModel = Backbone.Model.extend({
    defaults: {
	// container for available items
	apps:    new Canvas.AppCollection(),
	trials:  new Canvas.TrialCollection(),
	metrics: new Canvas.MetricCollection(),
	threads: new Canvas.ThreadCollection(),

	// index of selected items
	curApp:    -1,
	curTrial:  -1,
	curMetric: -1,
	curThread: -1,

	// above 4 items are all selected
	ready: false,

	// regex filter string for items above
	appFilter: "",
	trialFilter: "",
	metricFilter: "",
	threadFilter: "",

	// parameters in effect
	appName: undefined,
	trialId: undefined,
	metricId: undefined,
	threadId: undefined,

	// parameters above are actually valid
	valid: undefined,
    },

    flag: true,

    initialize: function() {
	this.on({
	    "change:curApp":    this.updateAppInfo,
	    "change:curTrial":  this.updateTrialInfo,
	    "change:curMetric": this.updateProfileInfo,
	    "change:curThread": this.updateProfileInfo,
	}, this);

	// get cached data source parameter
	this.cache = JSON.parse(localStorage.getItem('dscache')) || { };
    },

    // get cached parameter for current session
    getCache: function() {
	// get active session name
	var active = JSON.parse(localStorage.getItem('active'));

	if (active && this.cache[active]) {
	    var param = this.cache[active];

	    this.set("appName", param.appName);
	    this.set("trialId", param.trialId);
	    this.set("metricId", param.metricId);
	    this.set("threadId", param.threadId);
	}
    },

    // save cached parameter for current session
    putCache: function() {
	var curApp    = this.get("curApp");
	var curTrial  = this.get("curTrial");
	var curMetric = this.get("curMetric");
	var curThread = this.get("curThread");

	var appName  = this.get("apps").at(curApp).get("name");
	var trialId  = this.get("trials").at(curTrial).get("id");
	var metricId = this.get("metrics").at(curMetric).get("id");
	var threadId = this.get("threads").at(curThread).get("id");

	this.set("appName",  appName);
	this.set("trialId",  trialId);
	this.set("metricId", metricId);
	this.set("threadId", threadId);

	// get active session name
	var active = JSON.parse(localStorage.getItem('active'));

	if (active) {
	    this.cache[active] = {
		appName: appName,
		trialId: trialId,
		metricId: metricId,
		threadId: threadId,
	    };

	    localStorage.setItem('dscache', JSON.stringify(this.cache));
	}

	this.set("valid", true);
	this.trigger("ready");
    },

    fetch: function() {
	var self = this;
	var apps = this.get("apps");

	// get parameter from the cache
	this.getCache();

	apps.fetch().done(function() {
	    self.trigger("ready:apps");

	    if (self.get("valid")) {
		return;
	    }

	    // validate the parameter and select it if it's valid
	    for (var i=0; i<apps.models.length; i++) {
		if (apps.models[i].get("name") == self.get("appName")) {
		    self.set("curApp", i);
		    return;
		}
	    }

	    self.set("valid", false);
	});
    },

    updateAppInfo: function() {
	var self = this;
	var trials = this.get("trials");
	var curApp = this.get("curApp");

	// clear trial selection
	this.set("curTrial", -1);

	if (curApp >= 0) {
	    var appName = this.get("apps").at(curApp).get("name");

	    // get trial list for selected app
	    trials.update(appName).done(function() {
		self.trigger("ready:trials");
		

		if (self.get("valid")) {
		    return;
		}

		// validate the parameter and select it if it's valid
		for (var i=0; i<trials.models.length; i++) {
		    if (trials.models[i].get("id") == self.get("trialId")) {
			self.set("curTrial", i);
			return;
		    }
		}
	
		self.set("valid", false);
	    });

	} else {
	    trials.reset();
	}
    },

    updateTrialInfo: function() {
	var self = this;
	var metrics = this.get("metrics");
	var threads = this.get("threads");
	var curTrial = this.get("curTrial");

	// clear metric / thread selection
	this.set("curMetric", -1);
	this.set("curThread", -1);

	if (curTrial >= 0) {
	    var trialId = this.get("trials").at(curTrial).get("id");

	    // get metric list for selected trial
	    metrics.update(trialId).done(function() {
		self.trigger("ready:metrics");

		if (self.get("valid")) {
			self.trigger("ready:widgets");
		    return;
		}

		// validate the parameter and select it if it's valid
		for (var i=0; i<metrics.models.length; i++) {
		    if (metrics.models[i].get("id") == self.get("metricId")) {
			self.set("curMetric", i);
			return;
		    }
		}

		self.set("valid", false);
	    });

	    // get thread list for selected trial
	    threads.update(trialId).done(function() {
		self.trigger("ready:threads");

		if (self.get("valid")) {
		    return;
		}

		// validate the parameter and select it if it's valid
		for (var i=0; i<threads.models.length; i++) {
		    if (threads.models[i].get("id") == self.get("threadId")) {
			self.set("curThread", i);
			return;
		    }
		}

		self.set("valid", false);
	    });
	} else {
	    this.get("metrics").reset();
	    this.get("threads").reset();
	}

    },

    updateProfileInfo: function() {
	var curMetric = this.get("curMetric");
	var curThread = this.get("curThread");

	if (curMetric >= 0 && curThread >= 0) {

		var metricId = this.get("metrics").at(curMetric).get("id");
		var threadId = this.get("threads").at(curThread).get("id");
		this.set("metricId", metricId);
		this.set("threadId", threadId);

	    this.set("ready", true);

	    if (this.get("valid") === undefined) {
		// The only situation we can get here is to use cached
		// parameter, i.e. auto-login. So we can claim the
		// parameter as valid and ready.
		this.set("valid", true);
		this.trigger("ready");
	    }

	    //if profile info updates then trigger an event to sync profile collection
	    if(this.get("valid")){
	    	this.trigger("ready");
	    }
	} else {
	    this.set("ready", false);
	}
    },
});

Canvas.DSView = Backbone.View.extend({
    events: {
	"keyup input":             "updateFilter",
	"click div.panel-heading": "togglePanel",
	"click #collapseApp a":    "selectApp",
	"click #collapseTrial a":  "selectTrial",
	"click #collapseMetric a": "selectMetric",
	"click #collapseThread a": "selectThread",
	"click #dsReady":          "confirmDS",
    },

    updateFilter: function(evt) {
	var input = $("input", this.$el);

	// get CSS id of current open panel
	var id = $(".in", this.$el).attr("id");

	switch(evt.which) {
	case 13: // enter
	    input.blur();
	    break;
	case 27: // esc
	    if (input.val() == "") {
		input.blur();
		break;
	    } else {
		input.val("");
		// fall through
	    }
	default: // others
	    switch(id) {
	    case "collapseApp":
		this.model.set("appFilter", input.val());
		break;
	    case "collapseTrial":
		this.model.set("trialFilter", input.val());
		break;
	    case "collapseMetric":
		this.model.set("metricFilter", input.val());
		break;
	    case "collapseThread":
		this.model.set("threadFilter", input.val());
		break;
	    default:
		// do nothing if no panel is open
	    }

	    break;
	}

	evt.stopPropagation();
    },

    // toggle panel open or close
    _togglePanel: function(el) {
	var input = $("input", this.$el);
	var panels = $(".panel-group", this.$el);
	var target = $(el, panels);

	// load filter string from model
	switch(el) {
	case "#collapseApp":
	    input.val(this.model.get("appFilter"));
	    break;
	case "#collapseTrial":
	    input.val(this.model.get("trialFilter"));
	    break;
	case "#collapseMetric":
	    input.val(this.model.get("metricFilter"));
	    break;
	case "#collapseThread":
	    input.val(this.model.get("threadFilter"));
	    break;
	}

	// toggle the panel
	if (target.hasClass("in")) {
	    input.val("");
	    target.collapse("hide");
	} else {
	    $(".in", panels).collapse("hide");
	    target.collapse("show");
	}
    },

    togglePanel: function(evt) {
	var target = $(evt.currentTarget).attr("data-target");

	this._togglePanel(target);
	$("input", this.$el).focus();

	evt.stopPropagation();
    },

    enablePanel: function(el) {
	var panel = $(el, this.$el).parent();

	panel.removeClass("disabled panel-default");
	panel.addClass("panel-info");
    },

    disablePanel: function(el) {
	var panel = $(el, this.$el).parent();

	panel.removeClass("panel-info");
	panel.addClass("disabled panel-default");

	// disabled panel is always collapsed...
	$(el, this.$el).collapse("hide");

	// ... and doesn't have an active title
	$("h4", panel).html("");
    },

    selectApp: function(evt) {
	var idx = $(evt.currentTarget).attr("value");

	this.disablePanel("#collapseTrial");
	this.disablePanel("#collapseMetric");
	this.disablePanel("#collapseThread");

	this.model.set("curApp", idx);

	this._togglePanel("#collapseTrial");
    },

    selectTrial: function(evt) {
	var idx = $(evt.currentTarget).attr("value");

	this.disablePanel("#collapseMetric");
	this.disablePanel("#collapseThread");

	this.model.set("curTrial", idx);

	this._togglePanel("#collapseMetric");
    },

    selectMetric: function(evt) {
	var idx = $(evt.currentTarget).attr("value");

	this.model.set("curMetric", idx);

	if (this.model.get("curThread") >= 0) {
	    this._togglePanel("#collapseMetric");
	} else {
	    this._togglePanel("#collapseThread");
	}
    },

    selectThread: function(evt) {
	var idx = $(evt.currentTarget).attr("value");

	this.model.set("curThread", idx);

	if (this.model.get("curMetric") >= 0) {
	    this._togglePanel("#collapseThread");
	} else {
	    this._togglePanel("#collapseMetric");
	}
    },

    confirmDS: function() {
	this.model.putCache();
    },

    initialize: function() {
	this.template = _.template(
	    $("script.template#ds-template").html()
	);

	// the modal is by default:
	//   - hidden
	//   - not dismissible
	this.$el.modal({
	    backdrop: "static",
	    keyboard: false,
	    show: false,
	});

	// render the panel body when data is ready
	this.listenTo(this.model, "ready:apps", this.renderApps);
	this.listenTo(this.model, "ready:trials", this.renderTrials);
	this.listenTo(this.model, "ready:metrics", this.renderMetrics);
	this.listenTo(this.model, "ready:threads", this.renderThreads);

	// render the panel title when selection is changed
	this.listenTo(this.model, "change:curApp", this.renderAppsTitle);
	this.listenTo(this.model, "change:curTrial", this.renderTrialsTitle);
	this.listenTo(this.model, "change:curMetric", this.renderMetricsTitle);
	this.listenTo(this.model, "change:curThread", this.renderThreadsTitle);

	// enable confirm button if all data are ready
	this.listenTo(this.model, "change:ready", this.renderButton);

	// apply the filter when the filter string change
	this.listenTo(this.model, "change:appFilter", this.applyAppFilter);
	this.listenTo(this.model, "change:trialFilter", this.applyTrialFilter);
	this.listenTo(this.model, "change:metricFilter", this.applyMetricFilter);
	this.listenTo(this.model, "change:threadFilter", this.applyThreadFilter);

	// show modal if cache miss
	this.listenTo(this.model, "change:valid", this.toggle);
    },

    renderPanel: function(attr, el) {
	var models = this.model.get(attr).models;
	var collapse = $(el, this.$el);
	var heading = collapse.prev();

	collapse.html(this.template(models));
	heading.find("span").html(models.length);

	this.enablePanel(el);
    },

    renderApps: function() {
	this.renderPanel("apps", "#collapseApp");
    },

    renderTrials: function() {
	this.renderPanel("trials", "#collapseTrial");
    },

    renderMetrics: function() {
	this.renderPanel("metrics", "#collapseMetric");
    },

    renderThreads: function() {
	this.renderPanel("threads", "#collapseThread");
    },

    renderTitle: function(attr, idx, el) {
	if (idx < 0) {
	    return;
	}

	var heading = $(el, this.$el).prev();
	var name = this.model.get(attr).at(idx).get("name");

	heading.find("h4").html(name);
    },

    renderAppsTitle: function(model, value) {
	this.renderTitle("apps", value, "#collapseApp");
    },

    renderTrialsTitle: function(model, value) {
	this.renderTitle("trials", value, "#collapseTrial");
    },

    renderMetricsTitle: function(model, value) {
	this.renderTitle("metrics", value, "#collapseMetric");
    },

    renderThreadsTitle: function(model, value) {
	this.renderTitle("threads", value, "#collapseThread");
    },

    renderButton: function() {
	$("#dsReady", this.$el).prop("disabled", !this.model.get("ready"));
    },

    applyFilter: function(filter, el) {
	var regex = new RegExp(filter, "i");

	$(el, this.$el).find("a").each(function() {
	    if ($(this).text().search(regex) == -1) {
		$(this).hide();
	    } else {
		$(this).show();
	    }
	});
    },

    applyAppFilter: function(model, value) {
	this.applyFilter(value, "#collapseApp");
    },

    applyTrialFilter: function(model, value) {
	this.applyFilter(value, "#collapseTrial");
    },

    applyMetricFilter: function(model, value) {
	this.applyFilter(value, "#collapseMetric");
    },

    applyThreadFilter: function(model, value) {
	this.applyFilter(value, "#collapseThread");
    },

    // toggle the DS Modal
    toggle: function(model, value) {
	if (value == false) {
	    this.$el.modal("show");
	} else {
	    this.$el.modal("hide");
	    $("#dsCancel", this.$el).removeClass("hidden");
	}
    },
});

/////////////////////
//
// Metadata View

Canvas.MetadataView = Backbone.View.extend({
    initialize: function() {
	this.table = _.template(
            $("script.template#metadata-table-template").html()
        );

	this.loader = _.template(
            $("script.template#loader-template").html()
	);

	this.listenTo(this.collection, "fetch", this.renderLoader);
	this.listenTo(this.collection, "ready", this.renderTable);
    },

    renderLoader: function() {
	this.$el.html(this.loader(this.collection));
    },

    renderTable: function() {
	this.$el.html(this.table(this.collection));
    },
});

/////////////////////
//
// Profile View

Canvas.ProfileView = Backbone.View.extend({
    initialize: function() {
	this.table = _.template(
            $("script.template#profile-table-template").html()
        );

	this.loader = _.template(
            $("script.template#loader-template").html()
	);

	this.listenTo(this.collection, "fetch", this.renderLoader);
	this.listenTo(this.collection, "ready", this.renderTable);
    },

    renderLoader: function() {
	this.$el.html(this.loader(this.collection));
    },

    renderTable: function() {
	this.$el.html(this.table(this.collection));
    },
});


/////////////////////////
//
// D3 Bubble Chart View

Canvas.BubbleView = Backbone.View.extend({
    dia: 320,

    initialize: function() {
	this.bubble = d3.layout.pack()
	    .sort(null)
	    .size([this.dia-4, this.dia-4])
	    .padding(1.5)
	    .value(function(d) {
		return d.get("exclusive_percent");
	    });

	this.svg = d3.select(document.createElement("div"))
	    .append("svg")
	    .attr("width", this.dia)
	    .attr("height", this.dia);

	this.$el.html(this.svg.node());

	this.listenTo(this.model, "ready", this.render);
    },

    render: function() {
	var color = d3.scale.category20c();

	// Packed Data
	var data = this.bubble.nodes({
	    children: this.model.models,
	});

	// Data join
	var nodes = this.svg.selectAll("circle").data(data);

	// ENTER
	nodes.enter().append("circle");

	// EXIT
	nodes.exit().remove();

	// UPDATE + ENTER
	// Appending to the enter selection expands the update selection to include
	// entering elements; so, operations on the update selection after appending to
	// the enter selection will apply to both entering and updating nodes.
	nodes.transition().duration(500)
	    .attr("r", function(d) {return d.r;})
	    .attr("cx", function(d) {return d.x;})
	    .attr("cy", function(d) {return d.y;})
	    .style("fill", function(d) { return color(d.value); });

    },
});


/////////////////////////
//
// D3 Pie Chart View
Canvas.PieChartView = Backbone.View.extend({

	radius: 0,

	svg: null,

	initialize: function(){

		var width = 320;
		var height = 320;
		var sel = this.el.id;
		this.radius = Math.min(width, height) / 2;

		this.svg = d3.select("#" + sel)
  					.append('svg')
  					.attr('width', width)
  					.attr('height', height)
  					.append('g')
  					.attr('transform', 'translate(' + (width / 2) +  ',' + (height / 2) + ')');
 		

  		this.listenTo(this.model, "ready", this.render);
	},
	

	render: function(){

		var arc = d3.svg.arc().outerRadius(this.radius);
  		var pie = d3.layout.pie()
  					.value(function(d) { return d.get("exclusive_percent"); })
  					.sort(null);
  		var color = d3.scale.category20b();
		var path = this.svg.selectAll('path')
  					  .data(pie(this.model.models))
  					  .enter()
 					  .append('path')
  					  .attr('d', arc)
  					  .attr('fill', function(d, i) { 
                       		return color(d.data.id);
 					  });

	}

});

//function to draw bubble chart
//sel: 	 selector
//model: data source
//attri: attribute to retrive from data source
Canvas.drawBubble = function(sel, model, attri){

	var dia = 320;
	//clear the content specified by selector
	$("#"+sel).html("");

	var bubble = d3.layout.pack()
	    		   .sort(null)
	    		   .size([dia-4, dia-4])
	     		   .padding(1.5)
	               .value(function(d) {
						return d.get(attri);//exclusive_percent
	    			});

	var svg = d3.select(document.createElement("div"))
	    		.append("svg")
	    		.attr("width", dia)
	    		.attr("height", dia);

	$("#"+sel).html(svg.node());

	var color = d3.scale.category20c();
	// Packed Data
	var data = bubble.nodes({
	    children: model,
	});

	// Data join
	var nodes = svg.selectAll("circle").data(data);

	// ENTER
	nodes.enter().append("circle");

	// EXIT
	nodes.exit().remove();

	// UPDATE + ENTER
	// Appending to the enter selection expands the update selection to include
	// entering elements; so, operations on the update selection after appending to
	// the enter selection will apply to both entering and updating nodes.
	nodes.transition().duration(500)
	    .attr("r", function(d) {return d.r;})
	    .attr("cx", function(d) {return d.x;})
	    .attr("cy", function(d) {return d.y;})
	    .style("fill", function(d) { return color(d.value); });


};

//function to draw pie chart
Canvas.drawPie = function(sel, model, attri){

	var width = 320;
	var height = 320;
	var radius = Math.min(width, height) / 2;
	$("#" + sel).html("");
	var svg = d3.select("#" + sel)
  					.append('svg')
  					.attr('width', width)
  					.attr('height', height)
  					.append('g')
  					.attr('transform', 'translate(' + (width / 2) +  ',' + (height / 2) + ')');


  	var arc = d3.svg.arc().outerRadius(radius);
  	var pie = d3.layout.pie()
  				.value(function(d) { return d.get(attri); })
  				.sort(null);
  	var color = d3.scale.category20b();
	var path = svg.selectAll('path')
  				   .data(pie(model))
  				   .enter()
 				   .append('path')
  				   .attr('d', arc)
  				   .attr('fill', function(d, i) { 
                       	return color(d.data.id);
 					});

 		

};

//function to draw donut chart
Canvas.drawDonut = function(sel, model, attri){

	var width = 320;
    var height = 320;
    var radius = Math.min(width, height) / 2;
    var donutWidth = 50;                            

    var color = d3.scale.category20b();
    $("#" + sel).html("");
    var svg = d3.select('#'+sel)
      			.append('svg')
			    .attr('width', width)
			    .attr('height', height)
			    .append('g')
			    .attr('transform', 'translate(' + (width / 2) + ',' + (height / 2) + ')');

    var arc = d3.svg.arc()
			    .innerRadius(radius - donutWidth)             
			    .outerRadius(radius);
      
    var pie = d3.layout.pie()
		        .value(function(d) { return d.get(attri); })
		        .sort(null);

    var path = svg.selectAll('path')
			      .data(pie(model))
			      .enter()
			      .append('path')
			      .attr('d', arc)
			      .attr('fill', function(d, i) { 
			        return color(d.data.id);
			      });


}

/////////////////////////
//
// widget chart view
Canvas.WidgetChartView = Backbone.View.extend({

	events: {
		"click .pie" 	: "parser",
		"click .bubble" : "parser",
		"click .donut"	: "parser"
	},

	//chart type
	charType: undefined,
	//widget ID
	wid: undefined,

	initialize: function(){

  		this.listenTo(this.model, "ready", this.repaint);
	},

	parser: function(e){
		var className = e.target.className;
		this.charType = className;
		var id = $("#"+this.el.id+" > :nth-child(2)").attr("id");
		this.wid = id;
		this.draw(className, id);
	},

	draw: function(className, id){
		
		if(className == "pie"){
			Canvas.drawPie(id, this.collection.models, "exclusive_percent");
		}

		if(className == "bubble"){
			Canvas.drawBubble(id, this.collection.models, "exclusive_percent");
		}

		if(className == "donut"){
			Canvas.drawDonut(id, this.collection.models, "exclusive_percent");
		}
		
	},

	repaint: function(){
		if(this.charType != undefined && this.wid != undefined){
				this.draw(this.charType, this.wid);
		}
	},

});




//Metric dropdown list on widgets
Canvas.MetricDropdownView = Backbone.View.extend({

	events: {
		"click li a" : "updateMetric"
	},

	initialize: function(){
		this.model.fetch();	
		this.listenTo(this.model, "widget:metrics", this.render);
	},

	render: function(){
		var models = this.model.get("metrics").models;
		var dropdown = $(this.el);
		var template = _.template($("#widget-metric-template").html());
		dropdown.each(function(){
			$(this).html(template(models));
		});

	},

	updateMetric: function(evt){
		idx = evt.target.attributes[1].nodeValue;
		this.model.set("curMetric", idx);

	},

});

//thread dropdown list on widgets
Canvas.ThreadDropdownView = Backbone.View.extend({

	events: {
		"click li a" : "updateThread"
	},

	initialize: function(){
		//this.render();
		this.listenTo(this.model, "widget:threads", this.render);
	},

	render: function(){
		var models = this.model.get("threads").models;
		var dropdown = $(this.el);
		var template = _.template($("#widget-thread-template").html());
		dropdown.each(function(){
			$(this).html(template(models));
		});

	},

	updateThread: function(evt){
		idx = evt.target.attributes[1].nodeValue;
		this.model.set("curThread", idx);
	},
});

////////////////////////
//
// Widget Model

//Retrieve profile data for each widget
//similar to DSModel
Canvas.WidgetModel = Backbone.Model.extend({
	defaults: {
	// container for available items
	apps:    new Canvas.AppCollection(),
	trials:  new Canvas.TrialCollection(),
	metrics: new Canvas.MetricCollection(),
	threads: new Canvas.ThreadCollection(),
	//this is the combined data source for 
	//generating chart
	profile: new Canvas.ProfileCollection(),

	// index of selected items
	curApp:    -1,
	curTrial:  -1,
	curMetric: -1,
	curThread: -1,

	// above 4 items are all selected
	ready: false,

	// parameters in effect
	appName: undefined,
	trialId: undefined,
	metricId: undefined,
	threadId: undefined,

	// parameters above are actually valid
	valid: undefined,
    },

    initialize: function() {

	this.on({
	    "change:curApp":    this.updateAppInfo,
	    "change:curTrial":  this.updateTrialInfo,
	    "change:curMetric": this.updateProfileInfo,
	    "change:curThread": this.updateProfileInfo,
	}, this);

    },    

    fetch: function() {
	var self = this;
	var apps = this.get("apps");

	apps.fetch().done(function() {
	    //self.trigger("widget:apps");

	    if (self.get("valid")) {
		return;
	    }

	    self.updateAppInfo();

	    //self.set("valid", false);
	});
    },

    updateAppInfo: function() {
	var self = this;
	var trials = this.get("trials");
	var curApp = this.get("curApp");

	if (curApp >= 0) {
	    var appName = this.get("apps").at(curApp).get("name");

	    // get trial list for selected app
	    trials.update(appName).done(function() {

		if (self.get("valid")) {
		    return;
		}

		self.updateTrialInfo();

		//self.set("valid", false);
	    });
	} else {
	    trials.reset();
	}
    },

    updateTrialInfo: function() {
	var self = this;
	var metrics = this.get("metrics");
	var threads = this.get("threads");
	var curTrial = this.get("curTrial");

	// clear metric / thread selection
	this.set("curMetric", -1);
	this.set("curThread", -1);

	if (curTrial >= 0) {
	    var trialId = this.get("trials").at(curTrial).get("id");

	    // get metric list for selected trial
	    metrics.update(trialId).done(function() {
		self.trigger("widget:metrics");

		if (self.get("valid")) {
		    return;
		}

		/*
		// validate the parameter and select it if it's valid
		for (var i=0; i<metrics.models.length; i++) {
		    if (metrics.models[i].get("id") == self.get("metricId")) {
			self.set("curMetric", i);
			return;
		    }
		}
		*/

		//self.set("valid", false);
	    });

	    // get thread list for selected trial
	    threads.update(trialId).done(function() {
		self.trigger("widget:threads");

		if (self.get("valid")) {
		    return;
		}

		/*
		// validate the parameter and select it if it's valid
		for (var i=0; i<threads.models.length; i++) {
		    if (threads.models[i].get("id") == self.get("threadId")) {
			self.set("curThread", i);
			return;
		    }
		}
		*/

		//self.set("valid", false);
	    });
	} else {
	    this.get("metrics").reset();
	    this.get("threads").reset();
	}

    },

    updateProfileInfo: function() {
	var curMetric = this.get("curMetric");
	var curThread = this.get("curThread");

	if (curMetric >= 0 && curThread >= 0) {

		var metricId = this.get("metrics").at(curMetric).get("id");
		var threadId = this.get("threads").at(curThread).get("id");
		this.set("metricId", metricId);
		this.set("threadId", threadId);

	    this.set("ready", true);

	    if (this.get("valid") === undefined) {
		// The only situation we can get here is to use cached
		// parameter, i.e. auto-login. So we can claim the
		// parameter as valid and ready.
		this.set("valid", true);
		//this.trigger("ready");
	    }

	    //if profile info updates then sync profile collection
	   	this.get("profile").update(threadId, metricId);
	    
	} else {
	    this.set("ready", false);
	}
    },
});

////////////////////////
//
// Widget Manager view

//Widget manager view
//retrive "App" and "Trial"
//information from DS model and update 
//corresponding parameters in its child views
Canvas.WidgetMgrView = Backbone.View.extend({

	initialize: function(){

		var app 	= this.model.get("curApp");
		var trial 	= this.model.get("curTrial");

		//data source for each widget view
		//different instances to separate
		this.dsOne 		= new Canvas.WidgetModel({curApp: app, curTrial: trial});
		this.dsTwo 		= new Canvas.WidgetModel({curApp: app, curTrial: trial});
		this.dsThree	= new Canvas.WidgetModel({curApp: app, curTrial: trial});
		this.dsFour		= new Canvas.WidgetModel({curApp: app, curTrial: trial});

		//views for widgets
		//four instances of each view class
		this.widgetOneView = new Canvas.WidgetChartView({
			el: "#widgetOne",
			collection: this.dsOne.get("profile"),
		});

		this.widgetTwoView = new Canvas.WidgetChartView({
			el: "#widgetTwo",
			collection: this.dsTwo.get("profile"),
		});

		this.widgetThreeView = new Canvas.WidgetChartView({
			el: "#widgetThree",
			collection: this.dsThree.get("profile"),
		});

		this.widgetFourView = new Canvas.WidgetChartView({
			el: "#widgetFour",
			collection: this.dsFour.get("profile"),
		});

		//metric dropdown list views
		this.widgetMetricViewOne = new Canvas.MetricDropdownView({
			el: "#widgetOne .btnMetric .dropdown-menu",
			model: this.dsOne,
		});

		this.widgetMetricViewTwo = new Canvas.MetricDropdownView({
			el: "#widgetTwo .btnMetric .dropdown-menu",
			model: this.dsTwo,
		});

		this.widgetMetricViewThree = new Canvas.MetricDropdownView({
			el: "#widgetThree .btnMetric .dropdown-menu",
			model: this.dsThree,
		});

		this.widgetMetricViewFour = new Canvas.MetricDropdownView({
			el: "#widgetFour .btnMetric .dropdown-menu",
			model: this.dsFour,
		});

		//thread dropdown list views
		this.widgetThreadViewOne = new Canvas.ThreadDropdownView({
			el: "#widgetOne .btnThread .dropdown-menu",
			model: this.dsOne,
		});

		this.widgetThreadViewTwo = new Canvas.ThreadDropdownView({
			el: "#widgetTwo .btnThread .dropdown-menu",
			model: this.dsTwo,
		});
		
		this.widgetThreadViewThree = new Canvas.ThreadDropdownView({
			el: "#widgetThree .btnThread .dropdown-menu",
			model: this.dsThree,
		});

		this.widgetThreadViewFour = new Canvas.ThreadDropdownView({
			el: "#widgetFour .btnThread .dropdown-menu",
			model: this.dsFour,
		});

		this.listenTo(this.model, "ready:widgets", this.update);
	},


	update: function(){
		var app 	= this.model.get("curApp");
		var trial 	= this.model.get("curTrial");

		//update curApp & curTrial in each model
		//TODO: solve sync problem
		this.dsOne.set("curApp", app);
		this.dsTwo.set("curApp", app);
		this.dsThree.set("curApp", app);
		this.dsFour.set("curApp", app);
		this.dsOne.set("curTrial", trial);
		this.dsTwo.set("curTrial", trial);
		this.dsThree.set("curTrial", trial);
		this.dsFour.set("curTrial", trial);
	}

});


/////////////////////
//
// Global Model

Canvas.Model = Backbone.Model.extend({
    defaults: {
	// login model
	login: new Canvas.LoginModel(),

	// data source model
	ds: new Canvas.DSModel(),

	// collection of apps in taudb
	apps: new Canvas.AppCollection(),

	// collection of trials for selected app
	trials: new Canvas.TrialCollection(),

	// collection of metrics and threads for selected app && trial
	metrics: new Canvas.MetricCollection(),
	threads: new Canvas.ThreadCollection(),

	// collection of metadata for selected app && trial
	metadata: new Canvas.MetadataCollection(),

	// collection of profile for selected app && trial && metric && thread
	profile: new Canvas.ProfileCollection(),
    },

    initialize: function() {
	this.listenTo(this.get("login"), "ready", function() {
	    this.get("ds").fetch();
	});
	this.listenTo(this.get("ds"), "ready", this.update);
    },

    fetch: function() {
	// get login status
	this.get("login").fetch();
    },

    update: function() {
	var self = this;
	var ds = this.get("ds");
	var trialId  = ds.get("trialId");
	var threadId = ds.get("threadId");
	var metricId = ds.get("metricId");

	this.get("metadata").update(trialId);
	this.get("profile").update(threadId, metricId);
    },
});

/////////////////////
//
// Global View

Canvas.View = Backbone.View.extend({
    el: "body",

    //flag for initial widget manager view
    //when flag is true, initialize it
    //otherwise do nothing
    flag: true,

    events: {
	"click #logout": "logout",
    },

    initialize: function(options) {

    //initialize gridster
    //could be improved by using underscore.js
	var gridster = this.$(".gridster ul").gridster({
        widget_margins: [3, 3],
        widget_base_dimensions: [360, 380],
        min_cols: 2,
        max_cols: 2,
        min_rows: 2,
        max_rows: 2
    }).data('gridster');

	//add dropdown button in widget
	//hardcoded might be improved using template
    var btnChart = "<div class='btn-group btnChart'>"
  					+ "<button class='btn btn-default btn-sm dropdown-toggle' type='button' data-toggle='dropdown' aria-haspopup='true' aria-expanded='false'>"
    				+ "Chart Type <span class='caret'></span>"
  					+ "</button>"
  					+ "<ul class='dropdown-menu'>"
    				+ "<li><a href='#' class='pie'>Pie Chart</a></li>"
    				+ "<li><a href='#' class='bubble'>Bubble Chart</a></li>"
    				+ "<li><a href='#' class='donut'>Donut Chart</a></li>"
  					+ "</ul></div>";

  	var btnMetric = "<div class='btn-group btnMetric'>"
  					+ "<button class='btn btn-default btn-sm dropdown-toggle' type='button' data-toggle='dropdown' aria-haspopup='true' aria-expanded='false'>"
    				+ "Metrics <span class='caret'></span>"
  					+ "</button>"
  					+ "<ul class='dropdown-menu'>" 				
    			  	+ "</ul></div>";

    var btnThread = "<div class='btn-group btnThread'>"
  					+ "<button class='btn btn-default btn-sm dropdown-toggle' type='button' data-toggle='dropdown' aria-haspopup='true' aria-expanded='false'>"
    				+ "Thread <span class='caret'></span>"
  					+ "</button>"
  					+ "<ul class='dropdown-menu'>" 				
    			  	+ "</ul></div>";		  	

  	var panel = "<div class='inWigBtn'>"+ btnChart + btnThread + btnMetric + "</div>";

    var widgets = [
       ["<li id='widgetOne' class='front'>"+ panel + '<div id="w1"></div></li>', 1, 1, 1, 1],
       ["<li id='widgetTwo' class='behind'>"+ panel + '<div id="w2"></div></li>', 1, 1, 2, 1],
       ["<li id='widgetThree' class='front'>"+ panel + '<div id="w3"></div></li>', 1, 1, 1, 2],
       ["<li id='widgetFour' class='behind'>"+ panel + '<div id="w4"></div></li>', 1, 1, 2, 2],
    ];
    
    $.each(widgets, function(i, widget){
       gridster.add_widget.apply(gridster, widget)
    });

	// view for login modal
	this.loginView = new Canvas.LoginView({
	    el: ".modal#loginModal",
	    model: this.model.get("login"),
	});

	// view for data source modal
	this.dsView = new Canvas.DSView({
	    el: ".modal#dsModal",
	    model: this.model.get("ds"),
	});

	// view for metadata table
	this.metadataView = new Canvas.MetadataView({
	    el: ".main .tab-pane#metadata",
	    collection: this.model.get("metadata"),
	});

	// view for profile table
	this.profileView = new Canvas.ProfileView({
	    el: ".main .tab-pane#profile",
	    collection: this.model.get("profile"),
	});


	this.listenTo(this.model.get("login"), "ready", this.renderHeading);
	this.listenTo(this.model.get("ds"), "ready", this.renderStatus);

    },

    logout: function() {
	var loginModel = this.model.get("login");

	$.get("api/logout", function() {
	    location.reload();
	});
    },

    renderHeading: function() {
	var login = this.model.get("login");

	$(".navbar-fixed-top", this.$el).find(".navbar-text").html(
	    login.get("dbuser") + "@" +
	    login.get("dbhost") + ":" +
	    login.get("dbname")
	);
    },

    renderStatus: function() {

    	if(this.flag){
    		//view for dashboard
			this.widgetMgrView = new Canvas.WidgetMgrView({
				el: "#dashboard",
				model: this.model.get("ds"),
			});
			this.flag = false;
    	}

		var ds = this.model.get("ds");
		var ps = $("#status", this.$el).find("p");

		var appName = ds.get("apps").at(ds.get("curApp")).get("name");
		var trialName = ds.get("trials").at(ds.get("curTrial")).get("name");
		var metricName = ds.get("metrics").at(ds.get("curMetric")).get("name");
		var threadName = ds.get("threads").at(ds.get("curThread")).get("name");

		ps.eq(0).html(appName);
		ps.eq(1).html(trialName);
		ps.eq(2).html(metricName);
		ps.eq(3).html(threadName);
    },

});


/////////////////////
//
// Router

// Not used yet
Canvas.Router = Backbone.Router.extend({
    /*
    routes: {
	"tab/:name": "switchTab",
    },

    switchTab: function(name) {
	// toggle tab header
	$(".tab-header.active").toggleClass("active");
	$(".tab-header#tab-"+name).toggleClass("active");

	// toggle tab body
	$(".tab-body.active").toggleClass("active");
	$(".tab-body#tab-"+name).toggleClass("active");
    },
    */
});
