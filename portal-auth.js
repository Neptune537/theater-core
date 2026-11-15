document.addEventListener('DOMContentLoaded', () => {
  const button = document.getElementById('google-login-btn');
  button.textContent = 'Open Lite & sign in with Google';
  // Complete sign-in inside Lite so its in-memory bearer session survives.
  button.addEventListener('click', () => {
    window.location.assign('https://heavenlybound-lite.pages.dev/?signin=google');
  });
  const logout = document.getElementById('signout-btn');
  if (logout) logout.hidden = true;
  document.getElementById('signed-in-view').style.display = 'none';
  document.getElementById('signed-out-view').style.display = 'block';
  document.querySelectorAll('a[href="/game.html"]').forEach(link => {
    link.href = 'https://play.tr7n7t7.com/?venue=atlantis';
  });
});
