document.querySelectorAll(".dropdown").forEach(drop => {
  drop.addEventListener("click", () => {
    drop.classList.toggle("open");
  });
});

// رزرو غذا
function goToReserve(day){
  localStorage.setItem("reserveDay", day);
  window.location.href = "reserve-food.html";
}
function goToSalesPage() {
  window.location.href = 'sales.html';
}

// گزارشات
function loadReports(){
  window.location.href = "reports.html";
}

// کارت‌های داشبورد
function goToPage(page){
  const pages = {
    sales: "sales.html",
    restaurant: "restoranazad.html",
    "no-reserve": "no-reserve.html"
  };
  if(pages[page]) window.location.href = pages[page];
}

// تراکنش‌ها با دکمه‌های قبلی و بعدی
function loadTransactions() {
  const main = document.getElementById('mainContent');

  main.innerHTML = `
    <div class="search-box">
      <input type="text" id="searchInput" placeholder="🔍 جستجو در تراکنش‌ها">
    </div>
    <div style="overflow-x:auto; margin-top:10px;">
      <table id="transactionTable">
        <thead>
          <tr>
            <th>ردیف</th>
            <th>نوع تراکنش</th>
            <th>مقدار</th>
            <th>مانده</th>
            <th>تاریخ</th>
            <th>شرح</th>
          </tr>
        </thead>
        <tbody></tbody>
      </table>
    </div>
    <div class="pagination-container">
      <button id="prevBtn" class="page-btn">◀ قبلی</button>
      <span id="pageInfo"></span>
      <button id="nextBtn" class="page-btn">بعدی ▶</button>
    </div>
  `;

  const allTransactions = [
    { type: "افزودن اعتبار", amount: 500, date: "1398/6/1", desc: "شارژ اولیه" },
    { type: "کاهش اعتبار", amount: 120, date: "1398/6/2", desc: "ارسال پیام صوتی" },
    { type: "کاهش اعتبار", amount: 150, date: "1398/6/3", desc: "ارسال پیام صوتی" },
    { type: "افزودن اعتبار", amount: 300, date: "1398/6/4", desc: "شارژ اضافه" },
    { type: "کاهش اعتبار", amount: 200, date: "1398/6/5", desc: "تبدیل متن" },
    { type: "افزودن اعتبار", amount: 400, date: "1398/6/7", desc: "شارژ ویژه" },
    { type: "کاهش اعتبار", amount: 100, date: "1398/6/8", desc: "ارسال پیام" },
    { type: "افزودن اعتبار", amount: 250, date: "1398/6/9", desc: "شارژ" },
    { type: "کاهش اعتبار", amount: 80, date: "1398/6/10", desc: "پیام صوتی" }
  ];

  let filtered = [...allTransactions];
  const rowsPerPage = 5;
  let currentPage = 1;

  const tbody = document.querySelector("#transactionTable tbody");
  const prevBtn = document.getElementById("prevBtn");
  const nextBtn = document.getElementById("nextBtn");
  const pageInfo = document.getElementById("pageInfo");

  function renderTable() {
    tbody.innerHTML = "";
    let balance = 0;
    const start = (currentPage - 1) * rowsPerPage;
    const end = start + rowsPerPage;

    filtered.forEach((t, i) => {
      balance += t.type === "افزودن اعتبار" ? t.amount : -t.amount;
      if (i >= start && i < end) {
        tbody.innerHTML += `
          <tr>
            <td>${i+1}</td>
            <td>${t.type}</td>
            <td>${t.amount}</td>
            <td>${balance}</td>
            <td>${t.date}</td>
            <td class="description">${t.desc}</td>
          </tr>
        `;
      }
    });

    const totalPages = Math.ceil(filtered.length / rowsPerPage) || 1;
    pageInfo.innerText = `صفحه ${currentPage} از ${totalPages}`;

    prevBtn.disabled = currentPage === 1;
    nextBtn.disabled = currentPage === totalPages;
  }

  prevBtn.onclick = () => { if(currentPage>1){ currentPage--; renderTable(); } }
  nextBtn.onclick = () => { const totalPages=Math.ceil(filtered.length/rowsPerPage)||1; if(currentPage<totalPages){ currentPage++; renderTable(); } }

  document.getElementById("searchInput").addEventListener("input", e=>{
    const q=e.target.value.trim();
    filtered = allTransactions.filter(t=>t.type.includes(q)||t.desc.includes(q)||t.date.includes(q));
    currentPage=1;
    renderTable();
  });

  renderTable();
}

// منوی مالی
function goToFinance(action){
  if(action==='wallet'){ window.location.href='wallet.html'; }
  else if(action==='transactions'){ loadTransactions(); }
}

// ===================
// باز کردن صفحه رزرو غذا در تب جدید
// ===================
// در dashboard.js یا داخل تمپلیت
function openWeeklyReservations() {
    window.location.href = '{% url "menu:weekly_reservations" %}';
}
