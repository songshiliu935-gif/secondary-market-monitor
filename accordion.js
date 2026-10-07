const overviewBox=document.querySelector('#overviewEvents');
if(overviewBox){
  const collapse=()=>overviewBox.querySelectorAll('.event').forEach(card=>{
    const detail=document.createElement('details'); detail.className='change-item';
    detail.innerHTML=`<summary>${card.querySelector('h3').innerHTML}<span class="tag">${card.querySelector('.tag').innerHTML}</span></summary><div class="change-body">${Array.from(card.querySelectorAll('p')).map(p=>p.outerHTML).join('')}</div>`;
    card.replaceWith(detail);
  });
  new MutationObserver(collapse).observe(overviewBox,{childList:true}); collapse();
}
