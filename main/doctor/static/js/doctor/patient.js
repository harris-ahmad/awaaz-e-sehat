$('#vitalsContent').on('show.bs.collapse', function () {
    $('.vitals-header .fas').removeClass('fa-chevron-down').addClass('fa-chevron-up');
}).on('hide.bs.collapse', function () {
    $('.vitals-header .fas').removeClass('fa-chevron-up').addClass('fa-chevron-down');
});