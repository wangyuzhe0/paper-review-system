// 登录功能
if (document.getElementById('loginForm')) {
    document.getElementById('loginForm').onsubmit = async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const password = document.getElementById('password').value;
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({username, password})
        });
        const data = await res.json();
        if (res.ok) {
            window.location.href = 'dashboard.html';
        } else {
            document.getElementById('loginMessage').innerText = data.error || '登录失败';
        }
    }
}

// 注册功能
if (document.getElementById('registerForm')) {
    document.getElementById('registerForm').onsubmit = async function(e) {
        e.preventDefault();
        const username = document.getElementById('username').value;
        const email = document.getElementById('email').value;
        const password = document.getElementById('password').value;
        const role = document.getElementById('role').value;
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            credentials: 'include',
            body: JSON.stringify({username, email, password, role})
        });
        const data = await res.json();
        if (res.ok) {
            document.getElementById('registerMessage').style.color = '#27ae60';
            document.getElementById('registerMessage').innerText = '注册成功，请前往登录';
            setTimeout(() => { window.location.href = 'index.html'; }, 1200);
        } else {
            document.getElementById('registerMessage').style.color = '#e74c3c';
            document.getElementById('registerMessage').innerText = data.error || '注册失败';
        }
    }
}