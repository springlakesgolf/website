
(function(){
  var header=document.getElementById('header');
  if(header){
    if(header.classList.contains('page-mode')){header.classList.add('solid')}
    var onScroll=function(){if(!header.classList.contains('page-mode'))header.classList.toggle('scrolled',window.scrollY>60)};
    window.addEventListener('scroll',onScroll,{passive:true});onScroll();
  }
  var io=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target)}})},{threshold:.14,rootMargin:'0px 0px -8% 0px'});
  document.querySelectorAll('.reveal:not(.in)').forEach(function(el){io.observe(el)});
  var d=document.getElementById('drawer'),mt=document.getElementById('menuToggle'),dc=document.getElementById('drawerClose');
  if(mt){function o(){d.classList.add('open');d.setAttribute('aria-hidden','false');mt.setAttribute('aria-expanded','true')}
  function c(){d.classList.remove('open');d.setAttribute('aria-hidden','true');mt.setAttribute('aria-expanded','false')}
  mt.addEventListener('click',o);dc.addEventListener('click',c);
  d.querySelectorAll('a').forEach(function(a){a.addEventListener('click',c)});
  document.addEventListener('keydown',function(e){if(e.key==='Escape')c()})}
  document.querySelectorAll('.tee-link').forEach(function(a){a.addEventListener('click',function(ev){var w=window.open(a.href,'chronogolf','width=1024,height=880');if(w){ev.preventDefault();}});});
  document.querySelectorAll('.inquiry-form').forEach(function(f){f.addEventListener('submit',function(e){e.preventDefault();var n=f.querySelector('.form-note');if(n){n.style.display='block';n.textContent='Preview only. This form is not connected yet, so nothing was sent.';}})});
  document.querySelectorAll('.course-card,.tier-card').forEach(function(card){var lk=card.querySelector('a[href],button');if(lk){card.classList.add('is-clickable');card.addEventListener('click',function(e){if(e.target.closest('a,button,input,select,textarea,label'))return;if(lk.getAttribute('target')===String.fromCharCode(95)+'blank'){window.open(lk.href,'_blank','noopener');}else{lk.click();}});}else{card.classList.add('is-static');}});
})();
