
(function() {

var instance = openerp;
openerp.web.formats = {};

var _t = instance.web._t;

/**
 * Intersperses ``separator`` in ``str`` at the positions indicated by
 * ``indices``.
 *
 * ``indices`` is an array of relative offsets (from the previous insertion
 * position, starting from the end of the string) at which to insert
 * ``separator``.
 *
 * There are two special values:
 *
 * ``-1``
 *   indicates the insertion should end now
 * ``0``
 *   indicates that the previous section pattern should be repeated (until all
 *   of ``str`` is consumed)
 *
 * @param {String} str
 * @param {Array<Number>} indices
 * @param {String} separator
 * @returns {String}
 */
instance.web.intersperse = function (str, indices, separator) {
    separator = separator || '';
    var result = [], last = str.length;

    for(var i=0; i<indices.length; ++i) {
        var section = indices[i];
        if (section === -1 || last <= 0) {
            // Done with string, or -1 (stops formatting string)
            break;
        } else if(section === 0 && i === 0) {
            // repeats previous section, which there is none => stop
            break;
        } else if (section === 0) {
            // repeat previous section forever
            //noinspection AssignmentToForLoopParameterJS
            section = indices[--i];
        }
        result.push(str.substring(last-section, last));
        last -= section;
    }

    var s = str.substring(0, last);
    if (s) { result.push(s); }
    return result.reverse().join(separator);
};
/**
 * Insert "thousands" separators in the provided number (which is actually
 * a string)
 *
 * @param {String} num
 * @returns {String}
 */
instance.web.insert_thousand_seps = function (num) {
    var negative = num[0] === '-';
    num = (negative ? num.slice(1) : num);
    return (negative ? '-' : '') + instance.web.intersperse(
        num, _t.database.parameters.grouping, _t.database.parameters.thousands_sep);
};

/**
 * Check with a scary heuristic if the value is a bin_size or not.
 * If not, compute an approximate size out of the base64 encoded string.
 *
 * @param {String} value original format
 */
instance.web.binary_to_binsize = function (value) {
    if (!value) {
        return instance.web.human_size(0);
    }
    if (value.substr(0, 10).indexOf(' ') == -1) {
        // Computing approximate size out of base64 encoded string
        // http://en.wikipedia.org/wiki/Base64#MIME
        return instance.web.human_size(value.length / 1.37);
    } else {
        // already bin_size
        return value;
    }
};

/**
 * Returns a human readable size
 *
 * @param {Number} numner of bytes
 */
instance.web.human_size = function(size) {
    var units = _t("Bytes,Kb,Mb,Gb,Tb,Pb,Eb,Zb,Yb").split(',');
    var i = 0;
    while (size >= 1024) {
        size /= 1024;
        ++i;
    }
    return size.toFixed(2) + ' ' + units[i];
};

/**
 * Formats a single atomic value based on a field descriptor
 *
 * @param {Object} value read from OpenERP
 * @param {Object} descriptor union of orm field and view field
 * @param {Object} [descriptor.widget] widget to use to display the value
 * @param {Object} descriptor.type fallback if no widget is provided, or if the provided widget is unknown
 * @param {Object} [descriptor.digits] used for the formatting of floats
 * @param {String} [value_if_empty=''] returned if the ``value`` argument is considered empty
 */
instance.web.format_value = function (value, descriptor, value_if_empty) {
    var l10n = _t.database.parameters;
    var date_format = instance.web.normalize_format(l10n.date_format);
    var time_format = instance.web.normalize_format(l10n.time_format)
    // If NaN value, display as with a `false` (empty cell)
    if (typeof value === 'number' && isNaN(value)) {
        value = false;
    }
    //noinspection FallthroughInSwitchStatementJS
    switch (value) {
        case '':
            if (descriptor.type === 'char' || descriptor.type === 'text') {
                return '';
            }
            console.warn('Field', descriptor, 'had an empty string as value, treating as false...');
            return value_if_empty === undefined ?  '' : value_if_empty;
        case false:
        case undefined:
        case Infinity:
        case -Infinity:
            return value_if_empty === undefined ?  '' : value_if_empty;
    }
    switch (descriptor.widget || descriptor.type || (descriptor.field && descriptor.field.type)) {
        case 'id':
            return value.toString();
        case 'integer':
            return instance.web.insert_thousand_seps(
                _.str.sprintf('%d', value));
        case 'float':
            var digits = descriptor.digits ? descriptor.digits : [69,2];
            digits = typeof digits === "string" ? py.eval(digits) : digits;
            var precision = digits[1];
            var formatted = _.str.sprintf('%.' + precision + 'f', value).split('.');
            formatted[0] = instance.web.insert_thousand_seps(formatted[0]);
            return formatted.join(l10n.decimal_point);
        case 'float_time':
            var pattern = '%02d:%02d';
            if (value < 0) {
                value = Math.abs(value);
                pattern = '-' + pattern;
            }
            var hour = Math.floor(value);
            var min = Math.round((value % 1) * 60);
            if (min == 60){
                min = 0;
                hour = hour + 1;
            }
            return _.str.sprintf(pattern, hour, min);
        case 'many2one':
            // name_get value format
            return value[1] ? value[1].split("\n")[0] : value[1];
        case 'one2many':
        case 'many2many':
            if (typeof value === 'string') {
                return value;
            }
            return _.str.sprintf(_t("(%d records)"), value.length);
        case 'datetime':
            if (typeof(value) == "string")
                value = moment(instance.web.auto_str_to_date(value));
            else {
                value = moment(value);
            }
            return value.format(date_format + ' ' + time_format);
        case 'date':
            if (typeof(value) == "string")
                value = moment(instance.web.str_to_date(value.substring(0,10)));
            else {
                value = moment(value);
            }
            return value.format(date_format);
        case 'time':
            if (typeof(value) == "string")
                value = moment(instance.web.auto_str_to_date(value));
            else {
                value = moment(value);
            }
            return value.format(time_format);
        case 'selection': case 'statusbar':
            // Each choice is [value, label]
            if(_.isArray(value)) {
                 return value[1];
            }
            var result = _(descriptor.selection).detect(function (choice) {
                return choice[0] === value;
            });
            if (result) { return result[1]; }
            return;
        default:
            return value;
    }
};

instance.web.parse_value = function (value, descriptor, value_if_empty) {
    var date_pattern = instance.web.normalize_format(_t.database.parameters.date_format),
        time_pattern = instance.web.normalize_format(_t.database.parameters.time_format);
    var date_pattern_wo_zero = date_pattern.replace('MM','M').replace('DD','D'),
        time_pattern_wo_zero = time_pattern.replace('HH','H').replace('mm','m').replace('ss','s');
    switch (value) {
        case false:
        case "":
            return value_if_empty === undefined ?  false : value_if_empty;
    }
    var tmp;
    switch (descriptor.widget || descriptor.type || (descriptor.field && descriptor.field.type)) {
        case 'integer':
            do {
                tmp = value;
                value = value.replace(instance.web._t.database.parameters.thousands_sep, "");
            } while(tmp !== value);
            tmp = Number(value);
            // do not accept not numbers or float values
            if (isNaN(tmp) || tmp % 1)
                throw new Error(_.str.sprintf(_t("'%s' is not a correct integer"), value));
            return tmp;
        case 'float':
            tmp = Number(value);
            if (!isNaN(tmp))
                return tmp;

            var tmp2 = value;
            do {
                tmp = tmp2;
                tmp2 = tmp.replace(instance.web._t.database.parameters.thousands_sep, "");
            } while(tmp !== tmp2);
            var reformatted_value = tmp.replace(instance.web._t.database.parameters.decimal_point, ".");
            var parsed = Number(reformatted_value);
            if (isNaN(parsed))
                throw new Error(_.str.sprintf(_t("'%s' is not a correct float"), value));
            return parsed;
        case 'float_time':
            var factor = 1;
            if (value[0] === '-') {
                value = value.slice(1);
                factor = -1;
            }
            var float_time_pair = value.split(":");
            if (float_time_pair.length != 2)
                return factor * instance.web.parse_value(value, {type: "float"});
            var hours = instance.web.parse_value(float_time_pair[0], {type: "integer"});
            var minutes = instance.web.parse_value(float_time_pair[1], {type: "integer"});
            return factor * (hours + (minutes / 60));
        case 'progressbar':
            return instance.web.parse_value(value, {type: "float"});
        case 'datetime':
            var datetime = moment(value, [date_pattern + ' ' + time_pattern, date_pattern_wo_zero + ' ' + time_pattern_wo_zero], true)
            if (datetime.isValid())
                return instance.web.datetime_to_str(datetime.toDate());
            throw new Error(_.str.sprintf(_t("'%s' is not a correct datetime"), value));
        case 'date':
            var date = moment(value, [date_pattern, date_pattern_wo_zero], true)
            if (date.isValid())
                return instance.web.date_to_str(date.toDate());
            throw new Error(_.str.sprintf(_t("'%s' is not a correct date"), value));
        case 'time':
            var time = moment(value, [time_pattern, time_pattern_wo_zero], true);
            if (time.isValid())
                return instance.web.time_to_str(time.toDate());
            throw new Error(_.str.sprintf(_t("'%s' is not a correct time"), value));
    }
    return value;
};

instance.web.auto_str_to_date = function(value, type) {
    try {
        return instance.web.str_to_datetime(value);
    } catch(e) {}
    try {
        return instance.web.str_to_date(value);
    } catch(e) {}
    try {
        return instance.web.str_to_time(value);
    } catch(e) {}
    throw new Error(_.str.sprintf(_t("'%s' is not a correct date, datetime nor time"), value));
};

instance.web.auto_date_to_str = function(value, type) {
    switch(type) {
        case 'datetime':
            return instance.web.datetime_to_str(value);
        case 'date':
            return instance.web.date_to_str(value);
        case 'time':
            return instance.web.time_to_str(value);
        default:
            throw new Error(_.str.sprintf(_t("'%s' is not convertible to date, datetime nor time"), type));
    }
};

/**
 * performs a half up rounding with arbitrary precision, correcting for float loss of precision
 * See the corresponding float_round() in server/tools/float_utils.py for more info
 * @param {Number} the value to be rounded
 * @param {Number} a non zero precision parameter. eg: 0.01 rounds to two digits.
 */
instance.web.round_precision = function(value, precision){
    if(!value){
        return 0;
    }else if(!precision){
        throw new Error('round_precision(...):  Cannot round value: '+value+' with a precision of zero (or undefined)');
    }
    var normalized_value = value / precision;
    var epsilon_magnitude = Math.log(Math.abs(normalized_value))/Math.log(2);
    var epsilon = Math.pow(2, epsilon_magnitude - 53);
    normalized_value += normalized_value >= 0 ? epsilon : -epsilon;
    var rounded_value = Math.round(normalized_value);
    return rounded_value * precision;
};

/**
 * performs a half up rounding with a fixed amount of decimals, correcting for float loss of precision
 * See the corresponding float_round() in server/tools/float_utils.py for more info
 * @param {Number} the value to be rounded
 * @param {Number} the number of decimals. eg: round_decimals(3.141592,2) -> 3.14
 */
instance.web.round_decimals = function(value, decimals){
    return instance.web.round_precision(value, Math.pow(10,-decimals));
};

/**
+ * 
+ * convert python.strftime format into moment.js format
+ * inspired from : https://github.com/uruz/moment-datetime/blob/master/moment-datetime.js
+*/
instance.web.normalize_format = function(format){
    if (!format)
        return false;
    var replacements = {
            'a': 'ddd',
            'A': 'dddd',
            'b': 'MMM',
            'B': 'MMMM',
            //'c': //%c is defined too vaguely
            'd': 'DD',
            //'f': JS have no support for microseconds and moment.js have no support for milliseconds
            'H': 'HH',
            'I': 'hh',
            'j': 'DDDD',
            'm': 'MM',
            'M': 'mm',
            'p': 'A',
            'S': 'ss',
            'U': 'ww',//ww is for Sunday-based week
            'w': 'd',
            //'W': 'ww',//%W is weeknumber for weeks starting from Monday and it is not implemented in moment.js
            //'x':
            //'X': //%x and %X are defined too vaguely to be implemented 
            'y': 'YY',
            'Y': 'YYYY',
            'z': 'ZZ',
            //'Z': 'z', - moment.js does not support timezone names
            '%': '%'
    }
    var moment_format = '', directive_index = 0, replacement, unformatted;
    while (format.indexOf('%') !== -1){
        directive_index = format.indexOf('%') + 1;
        replacement = replacements[format[directive_index]];
        unformatted = format.substr(0, directive_index-1);
        if (unformatted.length){
                unformatted = '[' + unformatted.replace(/(\[|\])/g, '\\$&') +']';
        }
        moment_format += unformatted + (replacement ? replacement : format[directive_index]);
        format = format.substr(directive_index+1);
    }
    if (format.length){
        moment_format += '['+format+']';
    }
    return moment_format;
};

})();
