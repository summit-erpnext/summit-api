(()=>{frappe.templates.index=`<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title></title>
        <link rel="stylesheet" href="./index.css"/>
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css" 
        integrity="sha512-Kc323vGBEqzTmouAECnVceyQqyqdsSiqLQISBL29aUW4U/M7pSPA/gEUZQqv1cwx4OnYxTxve5UMg5GT6L4JJg==" crossorigin="anonymous" referrerpolicy="no-referrer" />
    </head>
    <body>
        <div id="chat-icon" class="chat-icon">
            <i class="fas fa-comment"></i>
        </div>

        <div id="chat-popup" class="chat-popup">

       <div class="chat-header">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="user-icon" fill="#d3d3d3">
            <path d="M406.5 399.6C387.4 352.9 341.5 320 288 320l-64 0c-53.5 0-99.4 32.9-118.5 79.6C69.9 362.2 48 311.7 48 256C48 141.1 141.1 48 256 48s208 93.1 208 208c0 55.7-21.9 106.2-57.5 143.6zm-40.1 32.7C334.4 452.4 296.6 464 256 464s-78.4-11.6-110.5-31.7c7.3-36.7 39.7-64.3 78.5-64.3l64 0c38.8 0 71.2 27.6 78.5 64.3zM256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zm0-272a40 40 0 1 1 0-80 40 40 0 1 1 0 80zm-88-40a88 88 0 1 0 176 0 88 88 0 1 0 -176 0z"/>
        </svg>
        
        <h4>Gen AI</h4> 
       </div>

       <div class="chat-content">
        <div class="message-input ">Hello! How can I help you?</div>
       </div>

       <div class="chat-footer">
        <input type="file" id="fileInput" />
        <label for="fileInput" class="upload-link">
            <i class="fa fa-paperclip" aria-hidden="true"></i>
        </label>


        <input type="text" id="chat-input" placeholder="Type message"/>
        <button id="send-btn"><i class="fas fa-paper-plane"></i></button>
       </div>

        </div>
        </div>
        <script src="./index.js"><\/script>
    </body>
</html>





`;var t=document.getElementById("chat-icon"),e=document.getElementById("chat-popup");t.addEventListener("click",()=>{e.style.display=e.style.display==="none"?"block":"none"});})();
//# sourceMappingURL=index.bundle.LJWCNK7I.js.map
