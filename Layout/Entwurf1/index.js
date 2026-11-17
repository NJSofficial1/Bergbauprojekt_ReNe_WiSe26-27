function addBlock() {
  let vis = document.getElementsByClassName("data-vis");
  let last = vis[vis.length - 1];
  let parent = last.parentNode;
  let node = last.cloneNode(true);

  const regex = "\\\"[0123456789]+";
  let numStr = node.innerHTML.match(regex)[0];
  let num = parseInt(numStr.slice(1), 10);
  node.innerHTML = node.innerHTML.replaceAll(num.toString(), (num + 1).toString());

  parent.appendChild(node);
  
}
