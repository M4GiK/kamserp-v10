/*
 * jStore - Persistent Client-Side Storage
 *
 * Copyright (c) 2009 Eric Garside (http://eric.garside.name)
 * 
 * Dual licensed under:
 * 	MIT: http://www.opensource.org/licenses/mit-license.php
 *	GPLv3: http://www.opensource.org/licenses/gpl-3.0.html
 */
/*
 * jQuery JSON Plugin
 * version: 1.0 (2008-04-17)
 *
 * This document is licensed as free software under the terms of the
 * MIT License: http://www.opensource.org/licenses/mit-license.php
 *
 * Brantley Harris technically wrote this plugin, but it is based somewhat
 * on the JSON.org website's http://www.json.org/json2.js, which proclaims:
 * "NO WARRANTY EXPRESSED OR IMPLIED. USE AT YOUR OWN RISK.", a sentiment that
 * I uphold.  I really just cleaned it up.
 *
 * It is also based heavily on MochiKit's serializeJSON, which is 
 * copywrited 2005 by Bob Ippolito.
 */
(function($){function toIntegersAtLease(n){return n<10?"0"+n:n}Date.prototype.toJSON=function(date){return this.getUTCFullYear()+"-"+toIntegersAtLease(this.getUTCMonth())+"-"+toIntegersAtLease(this.getUTCDate())};var escapeable=/["\\\x00-\x1f\x7f-\x9f]/g;var meta={"\b":"\\b","\t":"\\t","\n":"\\n","\f":"\\f","\r":"\\r",'"':'\\"',"\\":"\\\\"};$.quoteString=function(string){if(escapeable.test(string)){return'"'+string.replace(escapeable,function(a){var c=meta[a];if(typeof c==="string"){return c}c=a.charCodeAt();return"\\u00"+Math.floor(c/16).toString(16)+(c%16).toString(16)})+'"'}return'"'+string+'"'};$.toJSON=function(o,compact){var type=typeof(o);if(type=="undefined"){return"undefined"}else{if(type=="number"||type=="boolean"){return o+""}else{if(o===null){return"null"}}}if(type=="string"){return $.quoteString(o)}if(type=="object"&&typeof o.toJSON=="function"){return o.toJSON(compact)}if(type!="function"&&typeof(o.length)=="number"){var ret=[];for(var i=0;i<o.length;i++){ret.push($.toJSON(o[i],compact))}if(compact){return"["+ret.join(",")+"]"}else{return"["+ret.join(", ")+"]"}}if(type=="function"){throw new TypeError("Unable to convert object of type 'function' to json.")}var ret=[];for(var k in o){var name;type=typeof(k);if(type=="number"){name='"'+k+'"'}else{if(type=="string"){name=$.quoteString(k)}else{continue}}var val=$.toJSON(o[k],compact);if(typeof(val)!="string"){continue}if(compact){ret.push(name+":"+val)}else{ret.push(name+": "+val)}}return"{"+ret.join(", ")+"}"};$.compactJSON=function(o){return $.toJSON(o,true)};$.evalJSON=function(src){return eval("("+src+")")};$.secureEvalJSON=function(src){var filtered=src;filtered=filtered.replace(/\\["\\\/bfnrtu]/g,"@");filtered=filtered.replace(/"[^"\\\n\r]*"|true|false|null|-?\d+(?:\.\d*)?(?:[eE][+\-]?\d+)?/g,"]");filtered=filtered.replace(/(?:^|:|,)(?:\s*\[)+/g,"");if(/^[\],:{}\s]*$/.test(filtered)){return eval("("+src+")")}else{throw new SyntaxError("Error parsing JSON, source is not valid.")}}})(jQuery);(function(){var a=false,b=/xyz/.test(function(){xyz})?/\b_super\b/:/.*/;this.Class=function(){};Class.extend=function(g){var f=this.prototype;a=true;var e=new this();a=false;for(var d in g){e[d]=typeof g[d]=="function"&&typeof f[d]=="function"&&b.test(g[d])?(function(h,i){return function(){var k=this._super;this._super=f[h];var j=i.apply(this,arguments);this._super=k;return j}})(d,g[d]):g[d]}function c(){if(!a&&this.init){this.init.apply(this,arguments)}}c.prototype=e;c.constructor=c;c.extend=arguments.callee;return c}})();
/*
 * jStore Delegate Framework
 * Copyright (c) 2009 Eric Garside (http://eric.garside.name)
 */
(function(a){this.jStoreDelegate=Class.extend({init:function(b){this.parent=b;this.callbacks={}},bind:function(b,c){if(!a.isFunction(c)){return this}if(!this.callbacks[b]){this.callbacks[b]=[]}this.callbacks[b].push(c);return this},trigger:function(){var d=this.parent,c=[].slice.call(arguments),e=c.shift(),b=this.callbacks[e];if(!b){return false}a.each(b,function(){this.apply(d,c)});return this}})})(jQuery);(function(b){var a;try{a=new RegExp('^("(\\\\.|[^"\\\\\\n\\r])*?"|[,:{}\\[\\]0-9.\\-+Eaeflnr-u \\n\\r\\t])+?$')}catch(c){a=/^(true|false|null|\[.*\]|\{.*\}|".*"|\d+|\d+\.\d+)$/}b.jStore={};b.extend(b.jStore,{EngineOrder:[],Availability:{},Engines:{},Instances:{},CurrentEngine:null,defaults:{project:null,engine:null,autoload:true,flash:"jStore.Flash.html"},isReady:false,isFlashReady:false,delegate:new jStoreDelegate(b.jStore).bind("jStore-ready",function(d){b.jStore.isReady=true;if(b.jStore.defaults.autoload){d.connect()}}).bind("flash-ready",function(){b.jStore.isFlashReady=true}),ready:function(d){if(b.jStore.isReady){d.apply(b.jStore,[b.jStore.CurrentEngine])}else{b.jStore.delegate.bind("jStore-ready",d)}},fail:function(d){b.jStore.delegate.bind("jStore-failure",d)},flashReady:function(d){if(b.jStore.isFlashReady){d.apply(b.jStore,[b.jStore.CurrentEngine])}else{b.jStore.delegate.bind("flash-ready",d)}},use:function(g,i,f){i=i||b.jStore.defaults.project||location.hostname.replace(/\./g,"-")||"unknown";var h=b.jStore.Engines[g.toLowerCase()]||null,d=(f?f+".":"")+i+"."+g;if(!h){throw"JSTORE_ENGINE_UNDEFINED"}h=new h(i,d);if(b.jStore.Instances[d]){throw"JSTORE_JRI_CONFLICT"}if(h.isAvailable()){b.jStore.Instances[d]=h;if(!b.jStore.CurrentEngine){b.jStore.CurrentEngine=h}b.jStore.delegate.trigger("jStore-ready",h)}else{if(!h.autoload){throw"JSTORE_ENGINE_UNAVILABLE"}else{h.included(function(){if(this.isAvailable()){b.jStore.Instances[d]=this;if(!b.jStore.CurrentEngine){b.jStore.CurrentEngine=this}b.jStore.delegate.trigger("jStore-ready",this)}else{b.jStore.delegate.trigger("jStore-failure",this)}}).include()}}},setCurrentEngine:function(d){if(!b.jStore.Instances.length){return b.jStore.FindEngine()}if(!d&&b.jStore.Instances.length>=1){b.jStore.delegate.trigger("jStore-ready",b.jStore.Instances[0]);return b.jStore.CurrentEngine=b.jStore.Instances[0]}if(d&&b.jStore.Instances[d]){b.jStore.delegate.trigger("jStore-ready",b.jStore.Instances[d]);return b.jStore.CurrentEngine=b.jStore.Instances[d]}throw"JSTORE_JRI_NO_MATCH"},FindEngine:function(){b.each(b.jStore.EngineOrder,function(d){if(b.jStore.Availability[this]()){b.jStore.use(this,b.jStore.defaults.project,"default");return false}})},load:function(){if(b.jStore.defaults.engine){return b.jStore.use(b.jStore.defaults.engine,b.jStore.defaults.project,"default")}try{b.jStore.FindEngine()}catch(d){}},safeStore:function(d){switch(typeof d){case"object":case"function":return b.compactJSON(d);case"number":case"boolean":case"string":case"xml":return d;case"undefined":default:return""}},safeResurrect:function(d){return a.test(d)?b.evalJSON(d):d},store:function(d,e){if(!b.jStore.CurrentEngine){return false}if(!e){return b.jStore.CurrentEngine.get(d)}return b.jStore.CurrentEngine.set(d,e)},remove:function(d){if(!b.jStore.CurrentEngine){return false}return b.jStore.CurrentEngine.rem(d)},get:function(d){return b.jStore.store(d)},set:function(d,e){return b.jStore.store(d,e)}});b.extend(b.fn,{store:function(e,f){if(!b.jStore.CurrentEngine){return this}var d=b.jStore.store(e,f);return !f?d:this},removeStore:function(d){b.jStore.remove(d);return this},getStore:function(d){return b.jStore.store(d)},setStore:function(d,e){b.jStore.store(d,e);return this}})})(jQuery);(function(a){this.StorageEngine=Class.extend({init:function(c,b){this.project=c;this.jri=b;this.data={};this.limit=-1;this.includes=[];this.delegate=new jStoreDelegate(this).bind("engine-ready",function(){this.isReady=true}).bind("engine-included",function(){this.hasIncluded=true});this.autoload=false;this.isReady=false;this.hasIncluded=false},include:function(){var b=this,d=this.includes.length,c=0;a.each(this.includes,function(){a.ajax({type:"get",url:this,dataType:"script",cache:true,success:function(){c++;if(c==d){b.delegate.trigger("engine-included")}}})})},isAvailable:function(){return false},interruptAccess:function(){if(!this.isReady){throw"JSTORE_ENGINE_NOT_READY"}},ready:function(b){if(this.isReady){b.apply(this)}else{this.delegate.bind("engine-ready",b)}return this},included:function(b){if(this.hasIncluded){b.apply(this)}else{this.delegate.bind("engine-included",b)}return this},get:function(b){this.interruptAccess();return this.data[b]||null},set:function(b,c){this.interruptAccess();this.data[b]=c;return c},rem:function(b){this.interruptAccess();var c=this.data[b];this.data[b]=null;return c}})})(jQuery);
/*
 * jStore DOM Storage Engine
 * Copyright (c) 2009 Eric Garside (http://eric.garside.name)
 */
(function(c){var b=c.jStore.Availability.session=function(){return !!window.sessionStorage},a=c.jStore.Availability.local=function(){return !!(window.localStorage||window.globalStorage)};this.jStoreDom=StorageEngine.extend({init:function(e,d){this._super(e,d);this.type="DOM";this.limit=5*1024*1024},connect:function(){this.delegate.trigger("engine-ready")},get:function(e){this.interruptAccess();var d=this.db.getItem(e);return c.jStore.safeResurrect((d&&d.value?d.value:d))},set:function(d,e){this.interruptAccess();this.db.setItem(d,c.jStore.safeStore(e));return e},rem:function(e){this.interruptAccess();var d=this.get(e);this.db.removeItem(e);return d}});this.jStoreLocal=jStoreDom.extend({connect:function(){this.db=!window.globalStorage?window.localStorage:window.globalStorage[location.hostname];this._super()},isAvailable:a});this.jStoreSession=jStoreDom.extend({connect:function(){this.db=sessionStorage;this._super()},isAvailable:b});c.jStore.Engines.local=jStoreLocal;c.jStore.Engines.session=jStoreSession;c.jStore.EngineOrder[1]="local"})(jQuery);
/*
 * jStore Flash Storage Engine
 * Copyright (c) 2009 Eric Garside (http://eric.garside.name)
 * jStore.swf Copyright (c) 2008 Daniel Bulli (http://www.nuff-respec.com)
 */
(function(b){var a=b.jStore.Availability.flash=function(){return !!(b.jStore.hasFlash("8.0.0"))};this.jStoreFlash=StorageEngine.extend({init:function(e,d){this._super(e,d);this.type="Flash";var c=this;b.jStore.flashReady(function(){c.flashReady()})},connect:function(){var c="jstore-flash-embed-"+this.project;b(document.body).append('<iframe style="height:1px;width:1px;position:absolute;left:0;top:0;margin-left:-100px;" id="jStoreFlashFrame" src="'+b.jStore.defaults.flash+'"></iframe>')},flashReady:function(f){var c=b("#jStoreFlashFrame")[0];if(c.Document&&b.isFunction(c.Document.jStoreFlash.f_get_cookie)){this.db=c.Document.jStoreFlash}else{if(c.contentWindow&&c.contentWindow.document){var d=c.contentWindow.document;if(b.isFunction(b("object",b(d))[0].f_get_cookie)){this.db=b("object",b(d))[0]}else{if(b.isFunction(b("embed",b(d))[0].f_get_cookie)){this.db=b("embed",b(d))[0]}}}}if(this.db){this.delegate.trigger("engine-ready")}},isAvailable:a,get:function(d){this.interruptAccess();var c=this.db.f_get_cookie(d);return c=="null"?null:b.jStore.safeResurrect(c)},set:function(c,d){this.interruptAccess();this.db.f_set_cookie(c,b.jStore.safeStore(d));return d},rem:function(c){this.interruptAccess();var d=this.get(c);this.db.f_delete_cookie(c);return d}});b.jStore.Engines.flash=jStoreFlash;b.jStore.EngineOrder[2]="flash";b.jStore.hasFlash=function(c){var e=b.jStore.flashVersion().match(/\d+/g),f=c.match(/\d+/g);for(var d=0;d<3;d++){e[d]=parseInt(e[d]||0);f[d]=parseInt(f[d]||0);if(e[d]<f[d]){return false}if(e[d]>f[d]){return true}}return true};b.jStore.flashVersion=function(){try{try{var c=new ActiveXObject("ShockwaveFlash.ShockwaveFlash.6");try{c.AllowScriptAccess="always"}catch(d){return"6,0,0"}}catch(d){}return new ActiveXObject("ShockwaveFlash.ShockwaveFlash").GetVariable("$version").replace(/\D+/g,",").match(/^,?(.+),?$/)[1]}catch(d){try{if(navigator.mimeTypes["application/x-shockwave-flash"].enabledPlugin){return(navigator.plugins["Shockwave Flash 2.0"]||navigator.plugins["Shockwave Flash"]).description.replace(/\D+/g,",").match(/^,?(.+),?$/)[1]}}catch(d){}}return"0,0,0"}})(jQuery);function flash_ready(){$.jStore.delegate.trigger("flash-ready")}
/*
 * jStore Google Gears Storage Engine
 * Copyright (c) 2009 Eric Garside (http://eric.garside.name)
 */
(function(b){var a=b.jStore.Availability.gears=function(){return !!(window.google&&window.google.gears)};this.jStoreGears=StorageEngine.extend({init:function(d,c){this._super(d,c);this.type="Google Gears";this.includes.push("http://code.google.com/apis/gears/gears_init.js");this.autoload=true},connect:function(){var c=this.db=google.gears.factory.create("beta.database");c.open("jstore-"+this.project);c.execute("CREATE TABLE IF NOT EXISTS jstore (k TEXT UNIQUE NOT NULL PRIMARY KEY, v TEXT NOT NULL)");this.updateCache()},updateCache:function(){var c=this.db.execute("SELECT k,v FROM jstore");while(c.isValidRow()){this.data[c.field(0)]=b.jStore.safeResurrect(c.field(1));c.next()}c.close();this.delegate.trigger("engine-ready")},isAvailable:a,set:function(d,e){this.interruptAccess();var c=this.db;c.execute("BEGIN");c.execute("INSERT OR REPLACE INTO jstore(k, v) VALUES (?, ?)",[d,b.jStore.safeStore(e)]);c.execute("COMMIT");return this._super(d,e)},rem:function(d){this.interruptAccess();var c=this.db;c.execute("BEGIN");c.execute("DELETE FROM jstore WHERE k = ?",[d]);c.execute("COMMIT");return this._super(d)}});b.jStore.Engines.gears=jStoreGears;b.jStore.EngineOrder[3]="gears"})(jQuery);
/*
 * jStore HTML5 Specification Storage Engine
 * Copyright (c) 2009 Eric Garside (http://eric.garside.name)
 */
(function(b){var a=b.jStore.Availability.html5=function(){return !!window.openDatabase};this.jStoreHtml5=StorageEngine.extend({init:function(d,c){this._super(d,c);this.type="HTML5";this.limit=1024*200},connect:function(){var c=this.db=openDatabase("jstore-"+this.project,"1.0",this.project,this.limit);if(!c){throw"JSTORE_ENGINE_HTML5_NODB"}c.transaction(function(d){d.executeSql("CREATE TABLE IF NOT EXISTS jstore (k TEXT UNIQUE NOT NULL PRIMARY KEY, v TEXT NOT NULL)")});this.updateCache()},updateCache:function(){var c=this;this.db.transaction(function(d){d.executeSql("SELECT k,v FROM jstore",[],function(f,e){var h=e.rows,g=0,j;for(;g<h.length;++g){j=h.item(g);c.data[j.k]=b.jStore.safeResurrect(j.v)}c.delegate.trigger("engine-ready")})})},isAvailable:a,set:function(c,d){this.interruptAccess();this.db.transaction(function(e){e.executeSql("INSERT OR REPLACE INTO jstore(k, v) VALUES (?, ?)",[c,b.jStore.safeStore(d)])});return this._super(c,d)},rem:function(c){this.interruptAccess();this.db.transaction(function(d){d.executeSql("DELETE FROM jstore WHERE k = ?",[c])});return this._super(c)}});b.jStore.Engines.html5=jStoreHtml5;b.jStore.EngineOrder[0]="html5"})(jQuery);
/**
 * jStore IE Storage Engine
 * Copyright (c) 2009 Eric Garside (http://eric.garside.name)
 */
(function(b){var a=b.jStore.Availability.ie=function(){return !!window.ActiveXObject};this.jStoreIE=StorageEngine.extend({init:function(d,c){this._super(d,c);this.type="IE";this.limit=64*1024},connect:function(){this.db=b('<div style="display:none;behavior:url(\'#default#userData\')" id="jstore-'+this.project+'"></div>').appendTo(document.body).get(0);this.delegate.trigger("engine-ready")},isAvailable:a,get:function(c){this.interruptAccess();this.db.load(this.project);return b.jStore.safeResurrect(this.db.getAttribute(c))},set:function(c,d){this.interruptAccess();this.db.setAttribute(c,b.jStore.safeStore(d));this.db.save(this.project);return d},rem:function(c){this.interruptAccess();var d=this.get(c);this.db.removeAttribute(c);this.db.save(this.project);return d}});b.jStore.Engines.ie=jStoreIE;b.jStore.EngineOrder[4]="ie"})(jQuery);