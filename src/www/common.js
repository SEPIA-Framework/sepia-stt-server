//some useful functions for all tests and demos
function createModal(content, width, maxWidth){
	var layer = document.createElement("div");
	layer.className = "modal-layer";
	var modal = document.createElement("div");
	modal.className = "modal-box";
	if (width) modal.style.width = width;
	if (maxWidth) modal.style.maxWidth = maxWidth;
	if (typeof content == "string"){
		modal.innerHTML = content;
	}else{
		modal.appendChild(content);
	}
	document.body.appendChild(layer);
	layer.appendChild(modal);
	modal.closeModal = function(){
		layer.parentNode.removeChild(layer);
	}
	layer.addEventListener("click", function(e){
		if (e.target == layer){
			modal.closeModal();
		}
	});
	return modal;
}