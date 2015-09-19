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
    block = $(sel).find("."+this.name).data("-data-");
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
    this.head = $("<div class='head'><input class='txt' value="+this.name+"></div>");

    var ul = $("<ul class='OptionList'></ul>");
    var on_click = this.on_click;

    /* add list content, note that "this" will be masked in $.each() */
    $.each(this.data, function(index, entry) {
	var li;

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
    optionList = $(sel).find(".OptionList").data("OptionList");
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
    /* get application list */
    $.get("ajax/get_applications.php", cb_get_applications);
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
	$.get("ajax/get_trials.php",
    	      {
    		  "appName": app.active.value,
    	      },
    	      cb_get_trials);

    });
    app.fill("div#application");
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
	$.get("ajax/get_threads.php",
    	      {
    		  "trialId": trial.active.id,
    	      },
    	      cb_get_threads);
	$.get("ajax/get_metadata.php",
    	      {
    		  "trialId": trial.active.id,
    	      },
    	      cb_get_metadata);

    });

    trial.fill("div#trial");

    app.adopt(trial);
}

function cb_get_metadata(json) {
    var metadata = $("<table></table>");

    metadata.append("<tr><th>Key</th><th>Value</th></tr");

    $.each(json, function(name, value) {
	metadata.append("<tr><td>" + name + "</td><td>" + value + "</td></tr>");
    });

    $("div#metadata").html(metadata);
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
    });

    metric.fill("div#metric");

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
	var metric = $("div#metric .OptionList").data("OptionList");
	if ((metric.active != undefined) && (thread.active != undefined)) {
	    $.get("ajax/get_timers.php",
    		  {
		      "metricId": metric.active.id,
		      "threadId": thread.active.id,
		      "type"    : "exclusive",
    		  },
    		  cb_get_timers);
	}
    });

    thread.fill("div#thread");

    trial.adopt(thread);
}

function cb_get_timers(json) {
    var data = new Array;
    var metric = $("div#metric .OptionList").data("OptionList");
    var thread = $("div#thread .OptionList").data("OptionList");

    $.each(json, function(index, entry) {
	entry.exclusive_value   = parseFloat(entry.exclusive_value);
	entry.exclusive_percent = parseFloat(entry.exclusive_percent);
    });

    // d3_nodes(json);
    // d3_bubble(json);
    var bubble = new BubbleChart("timer",
			     metric.active.id,
			     thread.active.id,
			     json,
			     null,
			     function(d){return d.exclusive_percent;});
    bubble.fill("div#graph");

    var pie = new PieChart("timer",
			   metric.active.id,
			   thread.active.id,
			   json);
    pie.fill("div#pie");

    metric.adopt(bubble);
    metric.adopt(pie);

    /* show in a table */
    var timers = $("<table><tr><th>Name</th><th>value</th><th>Percent</th></tr></table");
    $("div#timer").html(timers);

    timer_append(json);
}

function timer_append(json) {
    var timers = $("div#timer table")
    $.each(json, function(index, entry) {
	timers.append("<tr><td>"+entry.short_name+"</td><td>"
		      +entry.exclusive_value+"</td><td>"
		      +entry.exclusive_percent+"</td></tr");
    });
}

function d3_nodes(data) {
    var width = 400,
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

/////////////////////// PieChart //////////////////////

var PieChart = function(name, metric, thread, data) {
    ElementBlock.call(this, "pie");

    var self = this;

    this.dia  = 400;
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

    this.dia  = 400;
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