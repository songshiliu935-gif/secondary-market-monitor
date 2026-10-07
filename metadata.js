(async function(){
  try{
    const response=await fetch('data/market_book.json?'+Date.now());
    if(!response.ok)return;
    const data=await response.json();
    const updated=data.updated_at_local||data.as_of||'—';
    const close=data.market_close_date?`${data.market_close_date} (US session)`:'Latest available close';
    const updatedNode=document.querySelector('#asOf');
    const closeNode=document.querySelector('#marketClose');
    if(updatedNode)updatedNode.innerHTML=`<span class="stamp-label">Updated</span> ${esc(updated)}`;
    if(closeNode)closeNode.innerHTML=`<span class="stamp-label">Market close</span> ${esc(close)}`;
  }catch(error){
    // The main dashboard remains usable if metadata cannot be loaded.
  }
})();
