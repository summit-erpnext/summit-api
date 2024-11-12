(() => {
  // frappe-html:/home/manoj/summit_open_v15/apps/summitapp/summitapp/public/js/templates/index.html
  frappe.templates["index"] = `<div id="chat-icon" class="chat-icon">
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







`;

  // ../summitapp/summitapp/public/js/chat_icon.js
  $(document).on("app_ready", function() {
    console.log("ChatUI Loaded");
    $("head").append(`
          <link
              rel="stylesheet"
              href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.6.0/css/all.min.css"
              integrity="sha512-Kc323vGBEqzTmouAECnVceyQqyqdsSiqLQISBL29aUW4U/M7pSPA/gEUZQqv1cwx4OnYxTxve5UMg5GT6L4JJg=="
              crossorigin="anonymous"
              referrerpolicy="no-referrer"
          />
      `);
    let main_section = $(document).find(".main-section");
    let chatIcon = $("<div>", {
      id: "chat-icon",
      class: "chat-icon"
    });
    let iComment = $("<i>", {
      class: "fas fa-comment"
    });
    chatIcon.append(iComment);
    let chatPopup = $("<div>", {
      id: "chat-popup",
      class: "chat-popup"
    });
    let chatHeader = $("<div>", {
      class: "chat-header"
    });
    let userIcon = $(`
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" class="user-icon" fill="#d3d3d3">
        <path d="M406.5 399.6C387.4 352.9 341.5 320 288 320l-64 0c-53.5 0-99.4 32.9-118.5 79.6C69.9 362.2 48 311.7 48 256C48 141.1 141.1 48 256 48s208 93.1 208 208c0 55.7-21.9 106.2-57.5 143.6zm-40.1 32.7C334.4 452.4 296.6 464 256 464s-78.4-11.6-110.5-31.7c7.3-36.7 39.7-64.3 78.5-64.3l64 0c38.8 0 71.2 27.6 78.5 64.3zM256 512A256 256 0 1 0 256 0a256 256 0 1 0 0 512zm0-272a40 40 0 1 1 0-80 40 40 0 1 1 0 80zm-88-40a88 88 0 1 0 176 0 88 88 0 1 0 -176 0z"/>
      </svg>
    `);
    let headerText = $("<h4>").text("Gen AI");
    chatHeader.append(userIcon).append(headerText);
    let chatContent = $("<div>", {
      class: "chat-content"
    });
    let messageInput = $("<div>", {
      class: "message-input",
      text: "Hello! How can I help you?"
    });
    chatContent.append(messageInput);
    let chatFooter = $("<div>", {
      class: "chat-footer"
    });
    let fileInput = $("<input>", {
      type: "file",
      id: "fileInput"
    });
    let fileLabel = $("<label>", {
      for: "fileInput",
      class: "upload-link"
    }).append(
      $("<i>", {
        class: "fa fa-paperclip",
        "aria-hidden": "true"
      })
    );
    let chatInput = $("<input>", {
      type: "text",
      id: "chat-input",
      placeholder: "Type message"
    });
    let sendButton = $("<button>", {
      id: "send-btn"
    }).append(
      $("<i>", {
        class: "fas fa-paper-plane"
      })
    );
    chatFooter.append(fileInput).append(fileLabel).append(chatInput).append(sendButton);
    chatPopup.append(chatHeader).append(chatContent).append(chatFooter);
    $(".main-section").append(chatIcon).append(chatPopup);
    $("#chat-icon").on("click", function() {
      $("#chat-popup").toggle();
    });
  });
})();
//# sourceMappingURL=summitapp.bundle.6BOPHWDT.js.map
