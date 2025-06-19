async function getCurrentUser() {
    const res = await fetch('/api/current_user', {credentials: 'include'});
    const data = await res.json();
    return data.user;
}

function showUserInfo(user) {
    const infoDiv = document.getElementById('userInfo');
    if (!user) {
        infoDiv.innerHTML = '<p>未登录，请<a href="index.html">登录</a></p>';
        document.getElementById('dashboardContent').innerHTML = '';
        document.getElementById('logoutBtn').style.display = 'none';
        return;
    }
    infoDiv.innerHTML = `<p>当前用户：<b>${user.username}</b>（${user.role}）</p>`;
    document.getElementById('logoutBtn').style.display = 'inline-block';
}

async function logout() {
    await fetch('/api/logout', {method: 'POST', credentials: 'include'});
    window.location.href = 'index.html';
}

document.getElementById('logoutBtn').onclick = logout;

window.onload = async function() {
    const user = await getCurrentUser();
    showUserInfo(user);
    if (!user) return;
    // 根据角色加载不同内容
    if (user.role === 'author') {
        document.getElementById('dashboardContent').innerHTML = `
            <h3>提交论文</h3>
            <form id="submitPaperForm">
                <label for="title">标题：</label>
                <input type="text" id="title" name="title" required>
                <label for="abstract">摘要：</label>
                <textarea id="abstract" name="abstract" required></textarea>
                <button type="submit">提交</button>
            </form>
            <div id="myPapers"></div>
        `;
        document.getElementById('submitPaperForm').onsubmit = async function(e) {
            e.preventDefault();
            const title = document.getElementById('title').value;
            const abstract = document.getElementById('abstract').value;
            const res = await fetch('/api/papers', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                credentials: 'include',
                body: JSON.stringify({title, abstract})
            });
            const data = await res.json();
            if (res.ok) {
                alert('论文提交成功');
                loadMyPapers();
            } else {
                alert(data.error || '提交失败');
            }
        };
        loadMyPapers();
    } else if (user.role === 'reviewer') {
        document.getElementById('dashboardContent').innerHTML = `
            <h3>分配给我的论文</h3>
            <div id="assignedPapers"></div>
        `;
        loadAssignedPapers();
    } else if (user.role === 'admin') {
        document.getElementById('dashboardContent').innerHTML = `
            <h3>所有论文管理</h3>
            <button id="assignBtn">自动分配论文</button>
            <div id="allPapers"></div>
        `;
        document.getElementById('assignBtn').onclick = triggerPaperAssignment;
        loadAllPapers();
    }
};

async function loadMyPapers() {
    const res = await fetch('/api/papers', {credentials: 'include'});
    const data = await res.json();
    if (res.ok) {
        let html = '<h4>我的论文</h4>';
        if (data.papers.length === 0) {
            html += '<p>暂无论文</p>';
        } else {
            html += '<ul>' + data.papers.map(p => `<li>${p.title}（状态：${p.status}）</li>`).join('') + '</ul>';
        }
        document.getElementById('myPapers').innerHTML = html;
    }
}

async function loadAssignedPapers() {
    const res = await fetch('/api/papers', {credentials: 'include'});
    const data = await res.json();
    if (res.ok) {
        let html = '';
        if (data.papers.length === 0) {
            html = '<p>暂无分配论文</p>';
        } else {
            html = '<ul>' + data.papers.map(p => `<li>${p.title}（状态：${p.status}）</li>`).join('') + '</ul>';
        }
        document.getElementById('assignedPapers').innerHTML = html;
    }
}

async function loadAllPapers() {
    const res = await fetch('/api/papers', {credentials: 'include'});
    const data = await res.json();
    if (res.ok) {
        let html = '';
        if (data.papers.length === 0) {
            html = '<p>暂无论文</p>';
        } else {
            html = '<ul>' + data.papers.map(p => `<li>${p.title}（作者ID：${p.author_id}，状态：${p.status}）</li>`).join('') + '</ul>';
        }
        document.getElementById('allPapers').innerHTML = html;
    }
}

async function triggerPaperAssignment() {
    const res = await fetch('/api/papers/assign', {method: 'POST', credentials: 'include'});
    const data = await res.json();
    if (res.ok) {
        alert('自动分配成功');
        loadAllPapers();
    } else {
        alert(data.error || '分配失败');
    }
}