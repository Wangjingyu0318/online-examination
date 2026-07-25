/**
 * AIProbe 在线考试与练习系统
 * 前端交互逻辑
 */

console.log('✅ AIProbe 系统 JS 已加载');

document.addEventListener('DOMContentLoaded', function() {
    const roleTabs = document.querySelectorAll('.role-tab');
    const loginForm = document.getElementById('loginForm');
    const loginBtn = document.getElementById('loginBtn');
    const studentFields = document.getElementById('studentFields');
    const adminFields = document.getElementById('adminFields');

    // ============================================================
    // 1. 角色切换
    // ============================================================
    roleTabs.forEach(function(tab) {
        tab.addEventListener('click', function() {
            // 切换Tab高亮
            roleTabs.forEach(function(t) { t.classList.remove('active'); });
            this.classList.add('active');

            // 获取角色
            const role = this.getAttribute('data-role');

            // 切换显示字段
            if (role === 'student') {
                studentFields.classList.remove('hidden');
                adminFields.classList.add('hidden');
                loginBtn.textContent = '身份核验并登录 →';
            } else {
                studentFields.classList.add('hidden');
                adminFields.classList.remove('hidden');
                loginBtn.textContent = '进入管理后台';
            }
        });
    });

    // ============================================================
    // 2. 登录表单提交
    // ============================================================
    if (loginForm) {
        loginForm.addEventListener('submit', function(e) {
            e.preventDefault();

            // 获取当前选中的角色
            const activeRole = document.querySelector('.role-tab.active');
            const role = activeRole ? activeRole.getAttribute('data-role') : 'student';

            // ==================== 考生登录 ====================
            if (role === 'student') {
                const name = document.getElementById('fullName').value.trim();
                const unit = document.getElementById('unit').value.trim();
                const phone = document.getElementById('phone').value.trim();
                const idNumber = document.getElementById('idNumber').value.trim();

                if (!name || !unit || !phone || !idNumber) {
                    alert('请完整填写所有字段');
                    return;
                }

                fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        role: 'student',
                        name: name,
                        unit: unit,
                        phone: phone,
                        idNumber: idNumber
                    })
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    if (data.code === 0) {
                        alert('🎓 考生登录成功！');
                        window.location.href = '/student/dashboard';
                    } else {
                        alert('❌ ' + data.message);
                    }
                })
                .catch(function(err) {
                    alert('网络错误，请重试');
                });
            }

            // ==================== 管理员登录 ====================
            else if (role === 'admin') {
                const username = document.getElementById('adminUsername').value.trim();
                const password = document.getElementById('adminPassword').value.trim();

                if (!username || !password) {
                    alert('请输入账号和密码');
                    return;
                }

                fetch('/api/auth/login', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        role: 'admin',
                        username: username,
                        password: password
                    })
                })
                .then(function(res) { return res.json(); })
                .then(function(data) {
                    if (data.code === 0) {
                        alert('⚙️ 管理后台登录成功！');
                        window.location.href = '/admin/dashboard';
                    } else {
                        alert('❌ ' + data.message);
                    }
                })
                .catch(function(err) {
                    alert('网络错误，请重试');
                });
            }
        });
    }
});