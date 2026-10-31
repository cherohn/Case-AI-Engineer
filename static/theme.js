const systemTheme = window.matchMedia('(prefers-color-scheme: dark)');
let theme = 'system';

try {
  const saved = localStorage.getItem('emporio-theme');
  if (['light', 'dark', 'system'].includes(saved)) theme = saved;
} catch {
  // The selector still works when browser storage is unavailable.
}

function applyTheme() {
  const dark = theme === 'dark' || (theme === 'system' && systemTheme.matches);
  document.documentElement.dataset.theme = dark ? 'dark' : 'light';
  document.querySelector('meta[name="theme-color"]').content = dark ? '#161d19' : '#faf8f3';
}

applyTheme();
systemTheme.addEventListener('change', applyTheme);

document.addEventListener('DOMContentLoaded', () => {
  const selector = document.querySelector('#theme');
  selector.value = theme;
  selector.addEventListener('change', () => {
    theme = selector.value;
    applyTheme();
    try {
      localStorage.setItem('emporio-theme', theme);
    } catch {
      // Keep the current choice for this page even if it cannot be saved.
    }
  });
});
