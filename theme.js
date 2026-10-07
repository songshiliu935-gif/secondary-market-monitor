const savedTheme=localStorage.getItem('market-book-theme');
if(savedTheme==='light')document.documentElement.classList.add('light-mode');
const themeButton=document.querySelector('#themeToggle');
function updateThemeButton(){themeButton.textContent=document.documentElement.classList.contains('light-mode')?'◐ Dark':'☀ Light'}
updateThemeButton();
themeButton.addEventListener('click',()=>{const light=document.documentElement.classList.toggle('light-mode');localStorage.setItem('market-book-theme',light?'light':'dark');updateThemeButton()});
