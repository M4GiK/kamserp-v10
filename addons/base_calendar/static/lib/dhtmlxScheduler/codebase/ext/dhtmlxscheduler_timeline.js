(function(){scheduler.matrix={};scheduler._merge=function(M,L){for(var N in L){if(typeof M[N]=="undefined"){M[N]=L[N]}}};scheduler.createTimelineView=function(O){scheduler._merge(O,{section_autoheight:true,name:"matrix",x:"time",y:"time",x_step:1,x_unit:"hour",y_unit:"day",y_step:1,x_start:0,x_size:24,y_start:0,y_size:7,render:"cell",dx:200,dy:50,_logic:function(S,R,Q){var P={};if(scheduler.checkEvent("onBeforeViewRender")){P=scheduler.callEvent("onBeforeViewRender",[S,R,Q])}return P}});if(scheduler.checkEvent("onTimelineCreated")){scheduler.callEvent("onTimelineCreated",[O])}scheduler[O.name+"_view"]=function(){scheduler.renderMatrix.apply(O,arguments)};var L=scheduler.render_data;scheduler.render_data=function(P,R){if(this._mode==O.name){if(R){for(var Q=0;Q<P.length;Q++){this.clear_event(P[Q]);this.render_timeline_event.call(this.matrix[this._mode],P[Q],0,true)}}else{C.call(O,true)}}else{return L.apply(this,arguments)}};scheduler.matrix[O.name]=O;scheduler.templates[O.name+"_cell_value"]=function(P){return P?P.length:""};scheduler.templates[O.name+"_cell_class"]=function(P){return""};scheduler.templates[O.name+"_scalex_class"]=function(P){return""};scheduler.templates[O.name+"_scaley_class"]=function(Q,R,P){return"class"};scheduler.templates[O.name+"_scale_label"]=function(Q,R,P){return R};scheduler.templates[O.name+"_tooltip"]=function(Q,P,R){return R.text};scheduler.templates[O.name+"_date"]=function(Q,P){if(Q.getDay()==P.getDay()&&Q-P<(24*60*60*1000)){return scheduler.templates.day_date(Q)}return scheduler.templates.week_date(Q,P)};scheduler.templates[O.name+"_scale_date"]=scheduler.date.date_to_str(O.x_date||scheduler.config.hour_date);scheduler.date["add_"+O.name]=function(Q,P,R){return scheduler.date.add(Q,(O.x_length||O.x_size)*P*O.x_step,O.x_unit)};scheduler.date[O.name+"_start"]=scheduler.date[O.x_unit+"_start"]||scheduler.date.day_start;scheduler.attachEvent("onSchedulerResize",function(){if(this._mode==O.name){C.call(O,true);return false}return true});scheduler.attachEvent("onOptionsLoad",function(){O.order={};for(var P=0;P<O.y_unit.length;P++){O.order[O.y_unit[P].key]=P}if(O.name==scheduler._mode){if(scheduler._date){scheduler.setCurrentView(scheduler._date,scheduler._mode)}}});scheduler.callEvent("onOptionsLoad",[O]);if(O.render!="cell"){var N=new Date();var M=(scheduler.date.add(N,1,O.x_unit).valueOf()-N.valueOf());scheduler["mouse_"+O.name]=function(U){var P=this._drag_event;if(this._drag_id){P=this.getEvent(this._drag_id);this._drag_event._dhx_changed=true}U.x-=O.dx;var T=0,S=0,Q=0;for(S;S<this._cols.length-1;S++){T+=this._cols[S];if(T>U.x){break}}T=0;for(Q;Q<this._colsS.heights.length;Q++){T+=this._colsS.heights[Q];if(T>U.y){break}}U.fields={};U.fields[O.y_property]=P[O.y_property]=O.y_unit[Q].key;U.x=Q/10000000;if(this._drag_mode=="new-size"&&P.start_date*1==this._drag_start*1){S++}if(S>=O._trace_x.length){var R=scheduler.date.add(O._trace_x[O._trace_x.length-1],O.x_step,O.x_unit)}else{var R=O._trace_x[S]}U.y=Math.round((R-this._min_date)/(1000*60*this.config.time_step));U.custom=true;U.shift=M;return U}}};scheduler.render_timeline_event=function(U,V,R){var N=E(U,false,this._step);var L=E(U,true,this._step);var P=scheduler.xy.bar_height;var T=2+V*P;var Q=scheduler.templates.event_class(U.start_date,U.end_date,U);Q="dhx_cal_event_line "+(Q||"");var O='<div event_id="'+U.id+'" class="'+Q+'" style="position:absolute; top:'+T+"px; left:"+N+"px; width:"+Math.max(0,L-N)+"px;"+(U._text_style||"")+'">'+scheduler.templates.event_bar_text(U.start_date,U.end_date,U)+"</div>";if(!R){return O}else{var S=document.createElement("DIV");S.innerHTML=O;var M=this.order[U[this.y_property]];var W=scheduler._els.dhx_cal_data[0].firstChild.rows[M].cells[1].firstChild;scheduler._rendered.push(S.firstChild);W.appendChild(S.firstChild)}};function K(){var N=scheduler.getEvents(scheduler._min_date,scheduler._max_date);var M=[];for(var O=0;O<this.y_unit.length;O++){M[O]=[]}if(!M[P]){M[P]=[]}for(var O=0;O<N.length;O++){var P=this.order[N[O][this.y_property]];var L=0;while(this._trace_x[L+1]&&N[O].start_date>=this._trace_x[L+1]){L++}while(this._trace_x[L]&&N[O].end_date>this._trace_x[L]){if(!M[P][L]){M[P][L]=[]}M[P][L].push(N[O]);L++}}return M}function E(S,Q,L){var T=0;var O=(Q)?S.end_date:S.start_date;if(O.valueOf()>scheduler._max_date.valueOf()){O=scheduler._max_date}var U=O-scheduler._min_date_timeline;if(U<0){M=0}else{var R=Math.round(U/(L*scheduler._cols[0]));if(R>scheduler._cols.length){R=scheduler._cols.length}for(var P=0;P<R;P++){T+=scheduler._cols[P]}var N=scheduler.date.add(scheduler._min_date_timeline,scheduler.matrix[scheduler._mode].x_step*R,scheduler.matrix[scheduler._mode].x_unit);U=O-N;var M=Math.floor(U/L)}T+=(Q)?M-14:M+1;return T}function A(S){var R="<table style='table-layout:fixed;' cellspacing='0' cellpadding='0'>";var Z=[];if(scheduler._load_mode&&scheduler._load()){return }if(this.render=="cell"){Z=K.call(this)}else{var T=scheduler.getEvents(scheduler._min_date,scheduler._max_date);for(var O=0;O<T.length;O++){var N=this.order[T[O][this.y_property]];if(!Z[N]){Z[N]=[]}Z[N].push(T[O])}}var Y=0;for(var P=0;P<scheduler._cols.length;P++){Y+=scheduler._cols[P]}var M=new Date();M=(scheduler.date.add(M,this.x_step*this.x_size,this.x_unit)-M)/Y;this._step=M;this._summ=Y;var V=scheduler._colsS.heights=[];for(var P=0;P<this.y_unit.length;P++){var Q=this._logic(this.render,this.y_unit[P],this);scheduler._merge(Q,{height:this.dy});if(this.section_autoheight){if(this.y_unit.length*Q.height<S.offsetHeight){Q.height=Math.max(Q.height,Math.floor((S.offsetHeight-1)/this.y_unit.length))}}scheduler._merge(Q,{tr_className:"",style_height:"height:"+Q.height+"px;",style_width:"width:"+(this.dx-1)+"px;",td_className:"dhx_matrix_scell "+scheduler.templates[this.name+"_scaley_class"](this.y_unit[P].key,this.y_unit[P].label,this),td_content:scheduler.templates[this.name+"_scale_label"](this.y_unit[P].key,this.y_unit[P].label,this),summ_width:"width:"+Y+"px;",table_className:""});R+="<tr class='"+Q.tr_className+"' style='"+Q.style_height+"'><td class='"+Q.td_className+"' style='"+Q.style_width+"'>"+Q.td_content+"</td>";if(this.render=="cell"){for(var O=0;O<scheduler._cols.length;O++){R+="<td class='dhx_matrix_cell "+scheduler.templates[this.name+"_cell_class"](Z[P][O],this._trace_x[O],this.y_unit[P])+"' style='width:"+(scheduler._cols[O]-1)+"px'><div style='width:"+(scheduler._cols[O]-1)+"px'>"+scheduler.templates[this.name+"_cell_value"](Z[P][O])+"<div></td>"}}else{R+="<td><div style='"+Q.summ_width+" "+Q.style_height+" position:relative;' class='dhx_matrix_line'>";if(Z[P]){Z[P].sort(function(d,c){return d.start_date>c.start_date?1:-1});var X=[];for(var O=0;O<Z[P].length;O++){var W=Z[P][O];var L=0;while(X[L]&&X[L].end_date>W.start_date){L++}X[L]=W;R+=scheduler.render_timeline_event.call(this,W,L)}}R+="<table class='"+Q.table_className+"' cellpadding='0' cellspacing='0' style='"+Q.summ_width+" "+Q.style_height+"' >";for(var O=0;O<scheduler._cols.length;O++){R+="<td class='dhx_matrix_cell "+scheduler.templates[this.name+"_cell_class"](Z[P],this._trace_x[O],this.y_unit[P])+"' style='width:"+(scheduler._cols[O]-1)+"px'><div style='width:"+(scheduler._cols[O]-1)+"px'><div></td>"}R+="</table>";R+="</div></td>"}R+="</tr>"}R+="</table>";this._matrix=Z;S.scrollTop=0;S.innerHTML=R;scheduler._rendered=[];var U=document.getElementsByTagName("DIV");for(var P=0;P<U.length;P++){if(U[P].getAttribute("event_id")){scheduler._rendered.push(U[P])}}for(var P=0;P<S.firstChild.rows.length;P++){V.push(S.firstChild.rows[P].offsetHeight)}}function D(N){N.innerHTML="<div></div>";N=N.firstChild;scheduler._cols=[];scheduler._colsS={height:0};this._trace_x=[];scheduler._min_date_timeline=scheduler._min_date;var R=scheduler._min_date;var Q=scheduler._x-this.dx-18;var P=this.dx;for(var L=0;L<this.x_size;L++){scheduler._cols[L]=Math.floor(Q/(this.x_size-L));this._trace_x[L]=new Date(R);scheduler._render_x_header(L,P,R,N);var M=scheduler.templates[this.name+"_scalex_class"](R);if(M){N.lastChild.className+=" "+M}R=scheduler.date.add(R,this.x_step,this.x_unit);Q-=scheduler._cols[L];P+=scheduler._cols[L]}var O=this._trace_x;N.onclick=function(S){var T=B(S);if(T){scheduler.callEvent("onXScaleClick",[T.x,O[T.x],S||event])}};N.ondblclick=function(S){var T=B(S);if(T){scheduler.callEvent("onXScaleDblClick",[T.x,O[T.x],S||event])}}}function C(M){if(M){scheduler.set_sizes();F();var L=scheduler._min_date;D.call(this,scheduler._els.dhx_cal_header[0]);A.call(this,scheduler._els.dhx_cal_data[0]);scheduler._min_date=L;scheduler._els.dhx_cal_date[0].innerHTML=scheduler.templates[this.name+"_date"](scheduler._min_date,scheduler._max_date);scheduler._table_view=true}}function H(){if(scheduler._tooltip){scheduler._tooltip.style.display="none";scheduler._tooltip.date=""}}function J(P,S,Q){if(P.render!="cell"){return }var R=S.x+"_"+S.y;var L=P._matrix[S.y][S.x];if(!L){return H()}L.sort(function(U,T){return U.start_date>T.start_date?1:-1});if(scheduler._tooltip){if(scheduler._tooltip.date==R){return }scheduler._tooltip.innerHTML=""}else{var O=scheduler._tooltip=document.createElement("DIV");O.className="dhx_tooltip";document.body.appendChild(O);O.onclick=scheduler._click.dhx_cal_data}var N="";for(var M=0;M<L.length;M++){N+="<div class='dhx_tooltip_line' event_id='"+L[M].id+"'>";N+="<div class='dhx_tooltip_date'>"+(L[M]._timed?scheduler.templates.event_date(L[M].start_date):"")+"</div>";N+="<div class='dhx_event_icon icon_details'>&nbsp;</div>";N+=scheduler.templates[P.name+"_tooltip"](L[M].start_date,L[M].end_date,L[M])+"</div>"}scheduler._tooltip.style.display="";scheduler._tooltip.style.top="0px";if(document.body.offsetWidth-Q.left-scheduler._tooltip.offsetWidth<0){scheduler._tooltip.style.left=Q.left-scheduler._tooltip.offsetWidth+"px"}else{scheduler._tooltip.style.left=Q.left+S.src.offsetWidth+"px"}scheduler._tooltip.date=R;scheduler._tooltip.innerHTML=N;if(document.body.offsetHeight-Q.top-scheduler._tooltip.offsetHeight<0){scheduler._tooltip.style.top=Q.top-scheduler._tooltip.offsetHeight+S.src.offsetHeight+"px"}else{scheduler._tooltip.style.top=Q.top+"px"}}function F(){dhtmlxEvent(scheduler._els.dhx_cal_data[0],"mouseover",function(M){var L=scheduler.matrix[scheduler._mode];if(L){var O=scheduler._locate_cell_timeline(M);var M=M||event;var N=M.target||M.srcElement;if(O){return J(L,O,getOffset(O.src))}}H()});F=function(){}}scheduler.renderMatrix=function(M){var L=scheduler.date[this.name+"_start"](scheduler._date);scheduler._min_date=scheduler.date.add(L,this.x_start*this.x_step,this.x_unit);scheduler._max_date=scheduler.date.add(scheduler._min_date,this.x_size*this.x_step,this.x_unit);scheduler._table_view=true;C.call(this,M)};function G(M){var N=M.parentNode.childNodes;for(var L=0;L<N.length;L++){if(N[L]==M){return L}}return -1}function B(N){N=N||event;var L=N.target?N.target:N.srcElement;while(L&&L.tagName!="DIV"){L=L.parentNode}if(L&&L.tagName=="DIV"){var M=L.className.split(" ")[0];if(M=="dhx_scale_bar"){return{x:G(L),y:-1,src:L,scale:true}}}}scheduler._locate_cell_timeline=function(O){O=O||event;var L=O.target?O.target:O.srcElement;while(L&&L.tagName!="TD"){L=L.parentNode}if(L&&L.tagName=="TD"){var N=L.className.split(" ")[0];if(N=="dhx_matrix_cell"){if(scheduler._isRender("cell")){return{x:L.cellIndex-1,y:L.parentNode.rowIndex,src:L}}else{var M=L.parentNode;while(M&&M.tagName!="TD"){M=M.parentNode}return{x:L.cellIndex,y:M.parentNode.rowIndex,src:L}}}else{if(N=="dhx_matrix_scell"){return{x:-1,y:L.parentNode.rowIndex,src:L,scale:true}}}}return false};var I=scheduler._click.dhx_cal_data;scheduler._click.dhx_cal_data=function(N){var L=I.apply(this,arguments);var M=scheduler.matrix[scheduler._mode];if(M){var O=scheduler._locate_cell_timeline(N);if(O){if(O.scale){scheduler.callEvent("onYScaleClick",[O.y,M.y_unit[O.y],N||event])}else{scheduler.callEvent("onCellClick",[O.x,O.y,M._trace_x[O.x],(((M._matrix[O.y]||{})[O.x])||[]),N||event])}}}return L};scheduler.dblclick_dhx_matrix_cell=function(M){var L=scheduler.matrix[scheduler._mode];if(L){var N=scheduler._locate_cell_timeline(M);if(N){if(N.scale){scheduler.callEvent("onYScaleDblClick",[N.y,L.y_unit[N.y],M||event])}else{scheduler.callEvent("onCellDblClick",[N.x,N.y,L._trace_x[N.x],(((L._matrix[N.y]||{})[N.x])||[]),M||event])}}}};scheduler.dblclick_dhx_matrix_scell=function(L){return scheduler.dblclick_dhx_matrix_cell(L)};scheduler._isRender=function(L){return(scheduler.matrix[scheduler._mode]&&scheduler.matrix[scheduler._mode].render==L)};scheduler.attachEvent("onCellDblClick",function(M,R,N,L,P){if(this.config.readonly||(P.type=="dblclick"&&!this.config.dblclick_create)){return }var Q=scheduler.matrix[scheduler._mode];var O={};O.start_date=Q._trace_x[M];O.end_date=(Q._trace_x[M+1])?Q._trace_x[M+1]:scheduler.date.add(Q._trace_x[M],Q.x_step,Q.x_unit);O[scheduler.matrix[scheduler._mode].y_property]=Q.y_unit[R].key;scheduler.addEventNow(O,null,P)});scheduler.attachEvent("onBeforeDrag",function(M,N,L){if(scheduler._isRender("cell")){return false}return true})})();