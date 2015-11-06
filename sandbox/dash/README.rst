======
Canvas
======

This is the brand new design of Canvas, a web frontend of TAUDB. This
design is based on backbone.js[1] and bootstrap[2].

Installation
============

Copy all the files and folders in this directory to your WWW
ROOT. Your web server should be configured so it can

* Understand PHP
* Query PostgreSQL with PHP
* Rewrite URL ([mod_rewrite](http://httpd.apache.org/docs/current/mod/mod_rewrite.html))

The URL rewrite is needed so our simple RESTful API implementation
could work. Note that there is a hidden file ".htaccess" in this
directory which tells Apache how to do the URL rewrite.

Features
========

* Login Dialog
* Session Control: When you login with a session name specified, your
  selected data source will be memorized in your broswer local
  storage. Next time when you login with the same session name, Canvas
  will try to select the memoriezed data source automaticlly.


Reference
=========

[1]. backbone.js: http://backbonejs.org/

[2]. bootstrap: http://getbootstrap.com/
