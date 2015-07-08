// Inserts shortcut buttons after all of the following:
//     <input type="text" class="vDateField">
//     <input type="text" class="vTimeField">

var DEBUG = false

var DatePickerHooks = {
    calendars: [],
    calendarInputFrom: [],
    calendarInputTo: [],
    calendarDivName: 'datePickerBox', // name of calendar <div> that gets toggled
    events: [],
    initialized: false,
    
    init: function() {
        DatePickerHooks.initialized = true
        DatePickerHooks.initDatePicker()
        DateTimeShortcuts._init()
    },
    
    initDatePicker: function() {
        DEBUG && console.log("DatePickerHooks.init")

        var inputs = document.getElementsByTagName('input');
        for (i=0; i<inputs.length; i++) {
            var inp = inputs[i];
            if (inp.getAttribute('type') == 'text' && inp.className.match(/vDateField/) || inp.className.match(/vDatePickerField/)) {
                DEBUG && console.log("addCalendar " + inp.id)
                if(inp.id.match(/from$/)) {
                  var from = inp;
                  var to = document.getElementById(inp.id.replace(/from$/,"")+"to")
                  if (to) {
                    DatePickerHooks.addCalendar(from, to);
                    // change className to prevent DateTimeShortcuts adding another calendar
                    from.className = from.className.replace(/vDateField/, "vDatePickerField")
                    to.className = to.className.replace(/vDateField/, "vDatePickerField")
                  }
                }
            }
        }      
    },
    
    updateDatePicker: function(num) {
        DEBUG && console.log(get_format('DATE_INPUT_FORMATS')[0])
        DEBUG && console.log("updateDatePicker " + num)
        var date_from, date_to;
        var date_str = jQuery(DatePickerHooks.calendarInputFrom[num]).val().split("-")
        if (date_str.length == 3) {
          date_from = new Date(date_str[0], date_str[1]-1, date_str[2])
        } else {
          var date_str = jQuery(DatePickerHooks.calendarInputFrom[num]).val().split(".")
          if (date_str.length == 3) {
            date_from = new Date(date_str[2], date_str[1]-1, date_str[0])
          } else {
            return
          }
        }
        date_str = jQuery(DatePickerHooks.calendarInputTo[num]).val().split("-")
        if (date_str.length == 3) {
          date_to = new Date(date_str[0], date_str[1]-1, date_str[2])
        } else {
          var date_str = jQuery(DatePickerHooks.calendarInputTo[num]).val().split(".")
          if (date_str.length == 3) {
            date_to = new Date(date_str[2], date_str[1]-1, date_str[0])
          } else {
            return
          }
        }
        
        jQuery('#'+DatePickerHooks.calendarDivName+num).DatePickerSetDate([date_from, date_to], true)
    },
    // Add calendar widget to a given field.
    addCalendar: function(from, to) {
        var num = DatePickerHooks.calendars.length;

        DatePickerHooks.calendarInputFrom[num] = from;
        DatePickerHooks.calendarInputTo[num] = to;

        var current_date = new Date();

        var cal_br = document.createElement('br');
        var cal_box = document.createElement('div');
        cal_box.className = 'datepicker-calendar'+num+' multi-field-box';
        cal_box.setAttribute('id', DatePickerHooks.calendarDivName + num);
        DEBUG && console.log("adding calendar " + num)
        
        if (from.className.match(/vDatePickerField/)) {
          jQuery(from).closest(".controls").find(".datepicker").remove()
        }
        else {
          jQuery(from).closest(".controls").append(cal_br)
        }
        jQuery(from).closest(".controls").append(cal_box)
        jQuery(from).unbind('change')
        jQuery(from).change(function() {DatePickerHooks.updateDatePicker(num)})
        jQuery(to).unbind('change')
        jQuery(to).change(function() {DatePickerHooks.updateDatePicker(num)})

        DatePickerHooks.calendars[num] = cal_box
        
        jQuery(cal_box).DatePicker({
          inline: true,
          date: [current_date, current_date],
          starts: 1,
          calendars: 3,
          mode: 'range',
          current: new Date(current_date.getFullYear(), current_date.getMonth(), 1),
          extraHeight: 4,
          extraWidth: 4,
          onChange: function(dates,el) {
            var format = get_format('DATE_INPUT_FORMATS')[0];
            // the format needs to be escaped a little
            format = format.replace('\\', '\\\\');
            format = format.replace('\r', '\\r');
            format = format.replace('\n', '\\n');
            format = format.replace('\t', '\\t');
            format = format.replace("'", "\\'");
            DEBUG && console.log(format)
            jQuery(from).attr('value', dates[0].strftime(format))
            jQuery(to).attr('value', dates[1].strftime(format))
          },
          onRenderCell: function(el, date) {
            if (date) {
              for (var i in DatePickerHooks.events) {
                if (date >= DatePickerHooks.events[i].from && date <= DatePickerHooks.events[i].to) {
                  return { 'className': DatePickerHooks.events[i].classtag.replace(/\s/g, "_") } 
                }
              }
            }
            return { 'className': "" } 
          },
        })
        DatePickerHooks.updateDatePicker(num)
    },
}
$(document).ready(function() {
  DEBUG && console.log("monkey-patch DateTimeShortcuts.init")
  removeEvent(window, 'load', DateTimeShortcuts.init);
  DateTimeShortcuts._init = DateTimeShortcuts.init;
  DateTimeShortcuts.init = DatePickerHooks.init;
  addEvent(window, 'load', DatePickerHooks.init);

  $.get('/crewdb/event_data', {}, function(data){
    DEBUG && console.log("got data")
    for (var i in data) {
      event = {}
//       remove timezoneValue, datepicker does not use utc
      tmp = new Date(data[i].date_from);
      event.from = new Date(tmp.getTime() + tmp.getTimezoneOffset() * 60 * 1000);
      tmp = new Date(data[i].date_to)
      event.to = new Date(tmp.getTime() + tmp.getTimezoneOffset() * 60 * 1000);
      event.classtag = data[i].description
      DEBUG && console.log("pushing" + event)
      DatePickerHooks.events.push(event)
    }
    if (DatePickerHooks.initialized) {
      DEBUG && console.log("reinit DatePicker")
      DatePickerHooks.initDatePicker()
    }
  }
);

})