(function(){
  function simplify(){
    document.querySelectorAll('.risk-card .note').forEach(node=>{
      const next=node.textContent.replace('60D z-score','Unusual move score');
      if(next!==node.textContent)node.textContent=next;
    });
    document.querySelectorAll('.event p,.change-body p').forEach(node=>{
      const next=node.innerHTML.replace(/equivalent to ([0-9.]+) standard deviations over the 60-day window\./g,'an unusually large move relative to the 60-day baseline (unusual-move score $1).');
      if(next!==node.innerHTML)node.innerHTML=next;
    });
  }
  simplify();
  let attempts=0;
  const timer=setInterval(()=>{
    simplify();
    attempts+=1;
    if(attempts>=8)clearInterval(timer);
  },250);
})();
