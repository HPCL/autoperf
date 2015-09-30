'use strict';

angular.module('myApp.view2', ['ngRoute'])

.config(['$routeProvider', function($routeProvider) {
  $routeProvider.when('/view2', {
    templateUrl: 'view2/view2.html',
    controller: 'View2Ctrl'
  });
}])

.controller('View2Ctrl', [function() {

}]);



var ElementBlock = function(name) {
    this.name     = name;
    this.parent   = null;
    this.children = [ ];
    this.div      = $("<div class="+name+"></div>");

    this.div.data("-data-", this);
}

ElementBlock.prototype.adopt = function(block) {
    if (block.parent != null) {
	block.parent.unadopt(block);
    }

    this.children.push(block);
    block.parent = this;

    return this;
}

ElementBlock.prototype.unadopt = function(block) {
    var i = this.children.indexOf(block);
    if (i != -1) {
	this.children.splice(i, 1);
	block.parent = null;
    }

    return this;
}

ElementBlock.prototype.appendTo = function(sel) {
    this.div.hide().appendTo($(sel)).fadeIn(200);

    return this;
}

ElementBlock.prototype.detach = function(sel) {
    this.children.forEach(function(child) {
	child.detach();
    });

    this.div.detach();
    return this;
}

ElementBlock.prototype.fill = function(sel) {
    var block = $(sel).find("."+this.name).data("-data-");
    if (block != undefined) {
	block.detach();
    }

    this.appendTo(sel);
    return this;
}

ElementBlock.prototype.show = function(speed) {
    this.div.show(speed);
    return this;
}

ElementBlock.prototype.hide = function(speed) {
    this.div.hide(speed);
    return this;
}



var OptionList = function(name, data, cb_click) {
    this.name     = name;
    this.data     = data;
    this.cb_click = cb_click;
    this.active   = undefined;
    this.parent   = undefined;
    this.children = [ ];
    this.head = $("<div class='head'><img class='search' src='css/images/search.png'/><input class='aptxt' value="+this.name+"></div>");
    
    var ul = $("<ul class='OptionList'></ul>");
    var on_click = this.on_click;


    // Default values for the different options
	var default_index = 0;
    if (name == "Thread")
        default_index = get_index(data,"Mean (No Null)");
    else if (name == "Metric")
        default_index = get_index(data, "TIME");
        if (default_index == 0) 
            default_index = get_index(data, "P_WALLCLOCK_TIME");


    /* add list content, note that "this" will be masked in $.each() */
    $.each(this.data, function(index, entry) {
	var li;

	if (index == default_index) {
		li = $("<li class='active'>" + entry.value + "</li>");
	} else 
	if (index%2) {
	    li = $("<li class='alt'>" + entry.value + "</li>");
	} else {
	    li = $("<li>" + entry.value + "</li>");
	}

	li.data("index", index);
   
	li.on("click", function() {
	    var optionList = $(this).parent().data("OptionList");

	    /* toggle "active" */
	    optionList.ul.find(".active").removeClass("active");
	    $(this).addClass("active");
	    optionList.active = optionList.data[$(this).data("index")];

	    /* call user callback */
	    optionList.cb_click(optionList);
	});

	li.appendTo(ul);
    });



    this.head.find("input").on("focus", function(evt) {
	$(this).val($(this).data("pattern"));
    });

    /* lose focus */
    this.head.find("input").on("blur", function(evt) {
	if ($(this).val() == "") {
	    $(this).val(name);
	} else {
	    $(this).val(name+" [ "+$(this).data("pattern")+" ]");
	}
    });

    /* interactive filter from user input */
    this.head.find("input").on("keyup", function(evt) {
	var pattern;
	$(this).data("pattern", $(this).val());

	switch (evt.which) {
	case 13: /* enter */
	    $(this).blur();
	    break;
	case 27: /* esc */
	    if ($(this).val() == "") {
		$(this).blur();
		break;
	    } else {
		$(this).val("");
		/* fall through */
	    }
	default:
	    /* filter by pattern match */
	    pattern = new RegExp($(this).val(), "i");
	    ul.children().each(function() {
		if ($(this).text().search(pattern) == -1) {
	    	    $(this).hide();
		} else {
	    	    $(this).show();
		}
	    });
	    break;
	}

	evt.stopPropagation();
    });

    this.ul = ul;
    this.ul.data("OptionList", this);
}

OptionList.prototype.set_default = function(optionList, dataArray) {
	
    var ind = 0;
    if (optionList.name == "Thread")
        ind = get_index(dataArray,"Mean (No Null)");
    else if (optionList.name == "Metric")
        ind = get_index(dataArray, "TIME");


	if (dataArray.length > 0) {
	    
	    //optionList.ul.find(".active").removeClass("active");
        $("#" + optionList.name.toLowerCase() + " li").eq(ind).addClass("active");

	    /* call user callback */
        optionList.active = dataArray[ind];
	    optionList.cb_click(optionList);
    }
}

OptionList.prototype.adopt = function(optionList) {
    this.children.push(optionList);
    optionList.parent = this;
}

OptionList.prototype.unadopt = function(optionList) {
    var i = this.children.indexOf(optionList);
    if (i != -1) {
	this.children.splice(i, 1);
	optionList.parent = undefined;
    }
}

OptionList.prototype.appendTo = function(sel) {
    this.head.hide().appendTo($(sel)).fadeIn(100);
    this.ul.hide().appendTo($(sel)).fadeIn(100);

    return this.ul;
}

OptionList.prototype.fill = function(sel) {
    var optionList = $(sel).find(".OptionList").data("OptionList");
    if (optionList != undefined) {
	optionList.detach();
    }
    this.appendTo(sel);
}

OptionList.prototype.detach = function() {
    this.children.forEach(function(child) {
	child.detach();
    });
    this.head.detach();
    this.ul.detach();
    return this.ul;
}

OptionList.prototype.setActive = function(id) {
    this.active = id;
}

OptionList.prototype.show = function(speed) {
    this.ul.show(speed);
    return this.ul;
}

OptionList.prototype.hide = function(speed) {
    this.ul.hide(speed);
    return this.ul;
}

// var OptionCategory = function(name) {
//     this.name = name;
//     this.list = { };
//     this.div  = $("<div id=" + name + "></div>");
// }

// OptionCategory.prototype.appendTo = function(sel) {
//     this.div.appendTo($(sel));
//     return this.div;
// }

// OptionCategory.prototype.addList = function(id, cb_get_list) {
//     if (this.list[id] == undefined) {
// 	this.list[id] = cb_get_list();
//     }

//     return this.list[id];
// }

function canvas_init() {
    top_menu_init();
    /* get application list */

    var defaultdb = ["brix.d.cs.uoregon.edu","geant4","geant4_collaborator"];
    $.get("ajax/get_applications.php", 
        { dbhost : defaultdb[0], dbname : defaultdb[1], dbuser : defaultdb[2] },
        cb_get_applications);
    update_dbinfo(defaultdb[0],defaultdb[1],defaultdb[2]);
}


function top_menu_init() {
    // DB Config
    var dbconfig_html = '  <p class="validateTips">All form fields are required.</p> \
  <form> \
    <fieldset> \
      <label for="hostname">Hostname</label> \
      <input type="text" name="hostname" id="hostname" value="brix.d.cs.uoregon.edu" class="text ui-widget-content ui-corner-all"> \
      <label for="dbname">Database name</label> \
      <input type="text" name="dbname" id="dbname" value="autoperfdb" class="text ui-widget-content ui-corner-all"> \
      <label for="dbusername">Username</label> \
      <input type="text" name="dbusername" id="dbusername" value="autoperf_user" class="text ui-widget-content ui-corner-all"> \
      <label for="password">Password</label> \
      <input type="password" name="password" id="password" value="xxxxxxx" class="text ui-widget-content ui-corner-all"> \
      <!-- Allow form submission with keyboard without duplicating the dialog button --> \
      <input type="submit" tabindex="-1" style="position:absolute; top:-1000px"> \
    </fieldset> \
  </form>';

    $( "div#dbconfig-dialog-form" ).html(dbconfig_html);

    var dialog, form,
      hostnameRegex = "^(([a-zA-Z0-9]|[a-zA-Z0-9][a-zA-Z0-9\-]*[a-zA-Z0-9])\.)*([A-Za-z0-9]|[A-Za-z0-9][A-Za-z0-9\-]*[A-Za-z0-9])$",
      hostname = $( "#hostname" ),
      dbname = $( "#dbname" ),
      dbuser = $( "#dbusername"),
      password = $( "#password" ),
      allFields = $( [] ).add( hostname ).add( dbname ).add( dbuser ).add( password ),
      tips = $( ".validateTips" );
      dialog = $( "#dbconfig-dialog-form" ).dialog({
        autoOpen: false,
        height: 300,
        width: 350,
        modal: true,
        buttons: {
          "Configure Database": setup_database,
            Cancel: function() {
            dialog.dialog( "close" );
            }
        },
        close: function() {
            form[ 0 ].reset();
            allFields.removeClass( "ui-state-error" );
        }
        });

    function setup_database() {
      var valid = true;
      allFields.removeClass( "ui-state-error" );
 
 /*
      valid = valid && checkLength( name, "username", 3, 16 );
      valid = valid && checkLength( email, "email", 6, 80 );
      valid = valid && checkLength( password, "password", 5, 16 );
 
      valid = valid && checkRegexp( name, /^[a-z]([0-9a-z_\s])+$/i, "Username may consist of a-z, 0-9, underscores, spaces and must begin with a letter." );
      valid = valid && checkRegexp( email, emailRegex, "eg. ui@jquery.com" );
      valid = valid && checkRegexp( password, /^([0-9a-zA-Z])+$/, "Password field only allow : a-z 0-9" );
 */
      if ( valid ) {

        //console.dir(allFields);
        $.get("ajax/get_applications.php", 
            { dbhost : allFields[0].value, dbname : allFields[1].value, dbuser : allFields[2].value, dbpass : allFields[3].value},
            cb_get_applications);

        update_dbinfo(allFields[0].value,allFields[1].value,allFields[2].value);
        dialog.dialog( "close" );
        
      }
      return valid;
    }

    dialog = $( "#dbconfig-dialog-form" ).dialog({
      autoOpen: false,
      height: 350,
      width: 350,
      modal: true,
      buttons: {
        "Configure Database": setup_database,
        Cancel: function() {
          dialog.dialog( "close" );
        }
      },
      close: function() {
        form[ 0 ].reset();
        allFields.removeClass( "ui-state-error" );
      }
    });
 
    form = dialog.find( "form" ).on( "submit", function( event ) {
      event.preventDefault();
      setup_database();
    });
 
    $( "#dbconfig" ).click(function() {
      dialog.dialog( "open" );
    });

}

function help() {
    // TODO
}

function update_dbinfo(hostname, dbname, dbuser) {
    $( ".dbinfo #database" ).html('Connected to ' + hostname + ', ' + dbuser + '@' + dbname);
}

function cb_get_applications(json) {
    var app;
    var data = new Array;

    $.each(json, function(index, value) {
	data.push(
	    {
		id: index,
		value: value,
	    }
	);
    });

    
    
    app = new OptionList("Application", data, function() {
        if (! app.active) app.active = data[0];
	   $.get("ajax/get_trials.php",
    	      {
    		  "appName": app.active.value,
    	      },
    	      cb_get_trials);

    });

	app.set_default(app, data);

    app.fill("div#application");

	//console.dir(app.active);
	
}

function cb_get_trials(json) {
    var trial;
    var data = new Array;
    var app = $("div#application .OptionList").data("OptionList");

    $.each(json, function(index, value) {
		data.push(
	  	  {
			id: index,
			value: value,
	  	  }
		);
    });
    

    trial = new OptionList("Trial", data, function() {
	$.get("ajax/get_metrics.php",
    	      {
    		  "trialId": trial.active.id,
    	      },
    	      cb_get_metrics);
    });

    trial.fill("div#trial");
    trial.set_default(trial, data);

    app.adopt(trial);
}


function cb_get_metrics(json) {
    var metric;
    var data = new Array;
    var trial = $("div#trial .OptionList").data("OptionList");

    $.each(json, function(index, value) {
	data.push(
	    {
		id: index,
		value: value,
	    }
	);
    });

    
    metric = new OptionList("Metric", data, function() {
	$.get("ajax/get_threads.php",
    	      {
    		  "trialId": trial.active.id,
    	      },
    	      cb_get_threads);
    });

    metric.fill("div#metric");
    metric.set_default(metric, data);

    trial.adopt(metric);
}

function cb_get_threads(json) {
    var thread;
    var data = new Array;
    var trial = $("div#trial .OptionList").data("OptionList");

    $.each(json, function(index, value) {
		data.push(
		    {
			id: index,
			value: value,
		    }
		);
    });

 	
    thread = new OptionList("Thread", data, function() {
    	$.get("ajax/get_metadata.php",
    	      {
    		  "trialId": trial.active.id,
    	      },
    	      cb_get_metadata);
    });

    thread.fill("div#thread");
    thread.set_default(thread,data);

    trial.adopt(thread);
}

function cb_get_metadata(json) {

	var metric = $("div#metric .OptionList").data("OptionList");
	var thread = $("div#thread .OptionList").data("OptionList");

	if ((metric.active != undefined) && (thread.active != undefined)) {

		$.get("ajax/get_timers.php",
	    	{
			    "metricId": metric.active.id,
			    "threadId": thread.active.id,
			    "type"    : "exclusive",
	    	},
	    	cb_get_timers);
	}


    var head = $("<div id='metadataheader'><table width='100%'><tr><td class='first'>Metadata Key</td><td class='head'>Metadata Value</td></tr></table></div>");
	$("div#metadataheader").html(head);

	var metadata = $("<table></table>");
    //metadata.append("<tr><th>Key</th><th>Value</th></tr");

    $.each(json, function(name, value) {
	metadata.append("<tr><td class='first'>" + name + "</td><td>" + value + "</td></tr>");
    });

    $("div#metadata").html(metadata);
}

function cb_get_timers(json) {
    var data = new Array;
    var metric = $("div#metric .OptionList").data("OptionList");
    var thread = $("div#thread .OptionList").data("OptionList");

    //console.dir(json);
    $.each(json, function(index, entry) {
    	entry.short_name = entry.short_name.replace("[SUMMARY] ","");
		entry.exclusive_value   = parseFloat(entry.exclusive_value);
		entry.exclusive_percent = parseFloat(entry.exclusive_percent);
    });


    /* show in a table */   
 	var head = $("<table width='400px'><tr><td class='head' width='200px'>Name</td><td class='head'>Value</td><td class='head'>Percent</td></tr></table>");
    $("div#timerheader").html(head);

    var timers = $("<table></table>");
    $("div#timer").html(timers);
    timer_append(json);

    // d3_nodes(json);
    // d3_bubble(json);
    $("div#graphheader").html($("<div id='graphheader'>Metric % Total</div>"));

    var bubble = new BubbleChart("timer",
			     metric.active.id,
			     thread.active.id,
			     json,
			     null,
			     function(d){return d.exclusive_percent;});
    bubble.fill("div#graph");
    metric.adopt(bubble);

	/*
    var pie = new PieChart("timer",
			   metric.active.id,
			   thread.active.id,
			   json);
    pie.fill("div#pie");

    metric.adopt(pie);
    */


 
}

function timer_append(json) {
    var timers = $("div#timer table")
    $.each(json, function(index, entry) {
	timers.append("<tr><td width='200px'>"+entry.short_name+"</td><td>"
		      +entry.exclusive_value.toPrecision(5)+"</td><td>"
		      +entry.exclusive_percent.toPrecision(5)+"</td></tr");
    });
}

function d3_nodes(data) {
    var width = 350,
	height = 300,
	radius = Math.min(width, height) / 2;

    var color = d3.scale.ordinal()
        .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);

    var svg = d3.select("div#graph")
	.append("svg")
        .attr("width", width)
        .attr("height", height);


    var inner = svg.append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

    var outter = svg.append("g")
        .attr("transform", "translate(" + width / 2 + "," + height / 2 + ")");

    var inner_arc = d3.svg.arc()
	.outerRadius(radius*2/3)
	.innerRadius(radius/3);

    var outter_arc = d3.svg.arc()
	.outerRadius(radius - 10)
	.innerRadius(radius*2/3+2);

    var pie = d3.layout.pie()
	.sort(null)
	.value(function(d) {return d.exclusive_percent;});

    var g1 = inner.selectAll(".arc")
    	.data(pie(data))
    	.enter().append("g")
    	.attr("class", "arc");

    g1.append("path")
    	.attr("d", inner_arc)
    	.style("fill", function(d) {return color(d.data.exclusive_value);});


    var g2 = outter.selectAll(".arc")
	.data(pie(data))
	.enter().append("g")
	.attr("class", "arc");

    g2.append("path")
	.attr("d", outter_arc)
	.style("fill", function(d) {return color(d.data.exclusive_value);});

    g2.append("title")
	.text(function(d) {return d.data.short_name;});

    $(".arc").on("click", function() {
	console.log(this);
	$(this).toggleClass("active");
    });
}

//////////////////////// Helpers /////////////////////
function get_index(dataArray, val) {
	//console.dir(dataArray);
	for (var i = 0; i < dataArray.length; i++) {
		if (dataArray[i].value == val) {
			return i;
		}
	}
	return 0;
}

function scrollIntoView(eleID) {
   var e = document.getElementById(eleID);
   if (!!e && e.scrollIntoView) {
       e.scrollIntoView();
   }
}

/////////////////////// PieChart //////////////////////

var PieChart = function(name, metric, thread, data) {
    ElementBlock.call(this, "pie");

    var self = this;

    this.dia  = 350;
    this.data = data;

    this.pie = d3.layout.pie()
	.sort(null)
	.value(function(d) {return d.exclusive_percent;});

    this.arc = d3.svg.arc()
	.outerRadius(this.dia / 2 -4)
	.innerRadius(50);

    this.svg = d3.select(document.createElement("div"))
	.append("svg")
	.attr("width", this.dia)
	.attr("height", this.dia)
	.attr("id", name);

    this.svg.append("g")
	.attr("transform", "translate(" + this.dia/2 + "," + this.dia/2 + ")");

    this.div.append(this.svg.node());

    this.div.on("mouseenter", "path", function(evt) {
	$("div#timer span").html($(this).find("title").text());
    });

    this.div.on("click", ".other", function(evt) {
	$.get("ajax/get_timers.php",
    	      {
		  "metricId": metric,
		  "threadId": thread,
		  "type"    : "exclusive",
		  "offset"  : self.data.length,
    	      },
    	      function(json){ self.append_data(json); });
    });

    this.update();
}

PieChart.prototype = Object.create(ElementBlock.prototype);

PieChart.prototype.update = function() {
    var sum = 0;
    var others = [ ];
    var color = d3.scale.ordinal()
        .range(["#98abc5", "#8a89a6", "#7b6888", "#6b486b", "#a05d56", "#d0743c", "#ff8c00"]);

    this.data.forEach(
	function(d) {
	    sum += d.exclusive_percent;
	},
	this
    );

    if (sum < 100) {
	others.push({
	    short_name : "Other...",
	    exclusive_value: -1,
	    exclusive_percent: 100 - sum,
	});
    }
    console.log("Pie: " + sum);

    /* Data Join */
    var nodes = this.svg.select("g").selectAll("path")
	.data(this.pie(this.data.concat(others)));

    /* ENTER */
    nodes.enter()
	.append("path")
	.attr("d", this.arc)
	.style("fill", function(d) {return color(d.data.exclusive_value);});

    /* EXIT */
    nodes.exit().remove();

    /* UPDATE + ENTER */
    nodes.attr("d", this.arc)
	.style("fill", function(d) {return color(d.data.exclusive_value);});

    nodes.append("title")
	.text(function(d) {return d.data.short_name;});

    this.div.find("path.other").attr("class", "");
    if (others.length != 0) {
	this.div.find("path:last").attr("class", "other");
    }
}

PieChart.prototype.append_data = function(json) {
    $.each(json, function(index, entry) {
	entry.exclusive_value   = parseFloat(entry.exclusive_value);
	entry.exclusive_percent = parseFloat(entry.exclusive_percent);
    });

    /* append new data */
    this.data.push.apply(this.data, json);

    this.update();
}


/////////////////////// BubbleChart //////////////////////

var BubbleChart = function(name, metric, thread, data, cb_get_new_data, cb_get_value) {
    ElementBlock.call(this, "bubble");

    var self = this;

    this.dia  = 350;
    this.data = data;
    this.cb_get_value = cb_get_value;

    this.bubble = d3.layout.pack()
	.sort(null)
	.size([this.dia-4, this.dia-4])
	.padding(1.5)
	.value(cb_get_value);

    this.svg = d3.select(document.createElement("div"))
	.append("svg")
	.attr("width", this.dia)
	.attr("height", this.dia)
	.attr("id", name);

    this.div.append(this.svg.node());

    this.div.on("mouseenter", "circle", function(evt) {
	$("div#timer span").html($(this).find("title").text());
    });

    this.div.on("click", "circle.other", function(evt) {
	$.get("ajax/get_timers.php",
    	      {
		  "metricId": metric,
		  "threadId": thread,
		  "type"    : "exclusive",
		  "offset"  : self.data.length,
    	      },
    	      function(json) {
		  timer_append(json);
		  self.append_data(json);
	      });
    });

    this.update();
}

BubbleChart.prototype = Object.create(ElementBlock.prototype); 

BubbleChart.prototype.update = function() {
    var sum = 0;
    var others = [ ];
    var color = d3.scale.category20c();

    this.data.forEach(
	function(d) {
	    sum += this.cb_get_value(d);
	},
	this
    );

    if (sum < 100) {
	others.push({
	    short_name : "Other...",
	    exclusive_value: -1,
	    exclusive_percent: 100 - sum,
	});
    }

    /* Data Join */
    var nodes = this.svg.selectAll("circle")
	.data(this.bubble.nodes({children: this.data.concat(others)}));

    /* ENTER */
    nodes.enter().append("circle");

    /* EXIT */
    nodes.exit().remove();

    /* UPDATE + ENTER */
    nodes.transition().duration(500)
	.attr("r", function(d) {return d.r;})
	.attr("cx", function(d) {return d.x;})
	.attr("cy", function(d) {return d.y;})
	.style("fill", function(d) { return color(d.exclusive_value); });

    nodes.append("title")
	.text(function(d) {return d.short_name;});

    this.div.find("circle:first").attr("class", "all");

    this.div.find("circle.other").attr("class", "");
    if (others.length != 0) {
	this.div.find("circle:last").attr("class", "other");
    }

}

BubbleChart.prototype.append_data = function(json) {
    $.each(json, function(index, entry) {
	entry.exclusive_value   = parseFloat(entry.exclusive_value);
	entry.exclusive_percent = parseFloat(entry.exclusive_percent);
    });

    /* append new data */
    this.data.push.apply(this.data, json);

    this.update();
}
