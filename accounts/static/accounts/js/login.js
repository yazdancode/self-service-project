document.getElementById("loginBtn").addEventListener("click", function () {

    const username = document.getElementById("username").value.trim();
    const password = document.getElementById("password").value.trim();

    if (username === "" || password === "") {
        alert("همه فیلدها را پر کنید");
        return;
    }

    // لاگین تستی
    if (username === "admin" && password === "1234") {

        localStorage.setItem("loggedIn", "true");
        window.location.href = "dashbord.html";

    } else {
        alert("نام کاربری یا رمز عبور اشتباه است");
    }
});
