/* Shared web authentication: no persistent bearer tokens or client-generated identity. */
(() => {
  let token = '', profile = null, expires = 0, configPromise, gisPromise, initialized = false, loginDialog;
  let receivingPeer = false;
  const peerOrigins = new Set(['https://heavenlysent-680ac.web.app','https://heavenlybound-lite.pages.dev','https://play.tr7n7t7.com','https://lite.tr7n7t7.com']);
  function shareSession(target, origin) {
    if(receivingPeer || !target || !peerOrigins.has(origin)) return false;
    target.postMessage(token && expires > Date.now()/1000
      ? {type:'kuroshio-auth-session',token,expires}
      : {type:'kuroshio-auth-clear'},origin);
    return true;
  }
  function embeddedParentOrigin() {
    if(window.parent===window || !window.parent) return '';
    try { const origin=new URL(document.referrer).origin; return peerOrigins.has(origin)?origin:''; } catch { return ''; }
  }
  window.addEventListener?.('message',async event=>{
    if(!peerOrigins.has(event.origin)) return;
    const frame=document.getElementById?.('pause-dashboard-frame');
    const fromFrame=Boolean(frame?.contentWindow && event.source===frame.contentWindow);
    const fromParent=Boolean(window.parent && window.parent!==window && event.source===window.parent && event.origin===embeddedParentOrigin());
    if(!fromFrame && !fromParent) return;
    if(event.data?.type==='kuroshio-auth-clear') {
      receivingPeer=true; try { clear(); } finally {receivingPeer=false;} return;
    }
    if(event.data?.type!=='kuroshio-auth-session' || !/^[0-9a-f]{64}$/.test(event.data.token || '') ||
      !Number.isFinite(event.data.expires) || event.data.expires<=Date.now()/1000) return;
    receivingPeer=true;
    try {
      const c=await config();
      const response=await fetch(c.apiOrigin+'/api/auth/me',{credentials:'omit',cache:'no-store',redirect:'error',headers:{Authorization:'Bearer '+event.data.token}});
      if(!response.ok) throw Error('Dashboard session is no longer valid');
      const me=await response.json();
      if(!me.principal_did?.startsWith('did:atlantis:')) throw Error('Invalid account response');
      token=event.data.token;expires=event.data.expires;
      profile={did:me.principal_did,wallet:base58(me.linked_solana_wallet),provider:'google'};emit();
    } catch(error) { emit(error.message); } finally { receivingPeer=false; }
  });
  const hex = bytes => Array.from(bytes, b => b.toString(16).padStart(2, '0')).join('');
  function base58(value) {
    if (!/^[0-9a-f]{64}$/i.test(value || '')) return '';
    const alphabet = '123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz';
    let n = BigInt('0x' + value), result = '';
    while (n) { result = alphabet[Number(n % 58n)] + result; n /= 58n; }
    for (let i = 0; i < value.length && value.slice(i, i + 2) === '00'; i += 2) result = '1' + result;
    return result;
  }
  function emit(error = '') {
    window.dispatchEvent(new CustomEvent('platform-auth-change', {detail: {profile, error}}));
    const parentOrigin=embeddedParentOrigin(); if(parentOrigin) shareSession(window.parent,parentOrigin);
  }
  function clear() { token = ''; profile = null; expires = 0; emit(); }
  async function config() {
    return configPromise ||= fetch('auth-config.json', {cache: 'no-store'}).then(async r => {
      if (!r.ok) throw Error('Account service is not configured');
      const c = await r.json();
      if (!c.apiOrigin || !c.googleClientId) throw Error('Account service is not configured');
      const url = new URL(c.apiOrigin);
      const local = ['localhost', '127.0.0.1', '[::1]'];
      if (url.username || url.password || url.search || url.hash || url.pathname !== '/' ||
          (url.protocol !== 'https:' && !(url.protocol === 'http:' && local.includes(url.hostname) && local.includes(location.hostname))))
        throw Error('Account API requires a trusted HTTPS origin');
      return {...c, apiOrigin: url.origin};
    });
  }
  async function request(path, body, authenticated = true) {
    const c = await config();
    if (authenticated && (!token || Date.now() / 1000 >= expires)) { clear(); throw Error('Sign in required'); }
    const r = await fetch(c.apiOrigin + path, {method: body === undefined ? 'GET' : 'POST',
      credentials: 'omit', cache: 'no-store', redirect: 'error',
      headers: {'Content-Type':'application/json', ...(authenticated ? {Authorization: 'Bearer ' + token} : {})},
      ...(body === undefined ? {} : {body: JSON.stringify(body)})});
    if (!r.ok) { if (r.status === 401) clear(); throw Error('Account request failed (' + r.status + ')'); }
    return r.status === 204 ? null : r.json();
  }
  async function acceptCredential(credential) {
    const s = await request('/api/auth/oidc', {id_token: credential}, false);
    if (!/^[0-9a-f]{64}$/.test(s.session_token || '') || !s.did?.startsWith('did:atlantis:') || !(s.expires_at_s > Date.now()/1000))
      throw Error('Invalid account response');
    token = s.session_token; expires = s.expires_at_s;
    profile = {did:s.did, wallet:base58(s.linked_solana_wallet), provider:'google'};
    loginDialog?.close(); loginDialog?.remove(); loginDialog = null; emit();
  }
  async function signIn(provider = 'google') {
    try {
      if (provider !== 'google') throw Error('Apple sign-in is not available yet');
      const c = await config();
      await (gisPromise ||= new Promise((resolve, reject) => {
        if (window.google?.accounts?.id) return resolve();
        const script = document.createElement('script'); script.src = 'https://accounts.google.com/gsi/client';
        script.onload = resolve; script.onerror = () => reject(Error('Google sign-in could not load')); document.head.append(script);
      }));
      if (!initialized) {
        google.accounts.id.initialize({client_id:c.googleClientId, use_fedcm_for_button:true,
          auto_select:false, button_auto_select:false,
          callback:r => acceptCredential(r.credential).catch(e => emit(e.message))});
        initialized = true;
      }
      if (loginDialog) { loginDialog.showModal(); return; }
      loginDialog = document.createElement('dialog');
      loginDialog.style.cssText = 'margin:auto;padding:24px;border:1px solid #27768c;border-radius:16px;background:#091726;color:#e8f8ff;z-index:10000';
      const title = document.createElement('p'); title.textContent = 'Sign in to Kuroshio';
      const host = document.createElement('div');
      const close = document.createElement('button'); close.textContent = 'Cancel';
      close.onclick = () => { loginDialog.close(); loginDialog.remove(); loginDialog = null; };
      loginDialog.append(title,host,close); document.body.append(loginDialog);
      google.accounts.id.renderButton(host,{theme:'outline',size:'large',text:'signin_with'});
      loginDialog.showModal();
    } catch(e) { emit(e.message); }
  }
  async function linkWallet() {
    try {
      if (!profile) throw Error('Sign in before linking a wallet');
      const wallet = window.solana;
      if (!wallet?.connect || !wallet?.signMessage) throw Error('A Solana wallet supporting message signatures is required');
      const connected = await wallet.connect();
      const bytes = connected.publicKey?.toBytes?.() || connected.publicKey?.toBuffer?.();
      if (!bytes || bytes.length !== 32) throw Error('Wallet public key unavailable');
      const challenge = await request('/api/auth/wallet-challenge', {principal_did:profile.did, wallet_pubkey_hex:hex(bytes)});
      if (challenge.principal_did !== profile.did || challenge.wallet_pubkey_hex !== hex(bytes)) throw Error('Wallet challenge mismatch');
      const message = `KUROSHIO_GYRE_WALLET_LINK_V1\ndid:${challenge.principal_did}\nwallet:${challenge.wallet_pubkey_hex}\nnonce:${challenge.nonce}\nexpires:${challenge.expires_at_s}`;
      const signed = await wallet.signMessage(new TextEncoder().encode(message), 'utf8');
      await request('/api/auth/link-wallet', {challenge, signature_hex:hex(signed.signature)});
      const me = await request('/api/auth/me'); profile = {did:me.principal_did, wallet:base58(me.linked_solana_wallet), provider:'google'}; emit();
    } catch(e) { emit(e.message); }
  }
  async function signOut(all = false) {
    try { if (token) await request('/api/auth/logout', {all_sessions:all}); clear(); }
    catch(e) { emit('Server logout failed; session remains active. Retry logout.'); }
  }
  window.PlatformAuth = Object.freeze({signIn, linkWallet, signOut, shareSession});
  setInterval(() => { if (token && Date.now()/1000 >= expires) clear(); }, 15000);
})();
