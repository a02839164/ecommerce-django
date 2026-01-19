

var message_timeout = document.getElementById('message-timer');
if(message_timeout){
    message_timeout.style.opacity = 1;

    setTimeout(function(){

    var fadeDuration = 2000; // 2秒淡出
        var interval = 50; // 每次改變透明度的間隔
        var fadeStep = interval / fadeDuration;

        var fadeOut = setInterval(function(){
            if(message_timeout.style.opacity > 0){
                message_timeout.style.opacity -= fadeStep;
            } else {
                clearInterval(fadeOut);
                message_timeout.style.display = 'none';
            }
        }, interval);

    },2000);
}