$(document).ready(function() {
    $('#calendar').fullCalendar({
        header: {
            left: 'prev,next today',
            center: 'title',
            right: 'month,agendaWeek,agendaDay'
        },
        events: '/fetch_service_requests/', // URL to fetch events from the backend
        eventRender: function(event, element) {
            element.qtip({
                content: event.description, // Show description on hover
                style: {
                    classes: 'qtip-bootstrap'
                }
            });
        }
    });
});