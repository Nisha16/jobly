$(function(){
    $('#profile_image').change( function(e) {

        var img = URL.createObjectURL(e.target.files[0]);
        $('.pimage').attr('src', img);
    });
});
