// موجودی کیف پول
let walletBalance = Number(localStorage.getItem('walletBalance')) || 0;
const walletDisplay = document.getElementById('walletBalance');
walletDisplay.innerText = walletBalance.toLocaleString();

const chargeBtn = document.getElementById('chargeBtn');
const chargeInput = document.getElementById('chargeAmount');
const suggestedAmounts = document.querySelectorAll('.suggested-amounts span');
const paymentForm = document.getElementById('paymentForm');
const paymentAmountInput = document.getElementById('paymentAmount');
const walletSound = document.getElementById('walletSound');

// انیمیشن افزایش موجودی
function animateWalletIncrease(amount) {
  const start = walletBalance;
  const end = walletBalance + amount;
  const duration = 500;
  let startTime = null;

  function animate(timestamp) {
    if (!startTime) startTime = timestamp;
    const progress = Math.min((timestamp - startTime) / duration, 1);
    const current = Math.floor(start + (end - start) * progress);
    walletDisplay.innerText = current.toLocaleString();
    walletDisplay.classList.add('bounce');
    if (progress < 1) {
      requestAnimationFrame(animate);
    } else {
      walletBalance = end;
      localStorage.setItem('walletBalance', walletBalance);
      setTimeout(() => walletDisplay.classList.remove('bounce'), 400);
    }
  }

  if(walletSound) { walletSound.currentTime = 0; walletSound.play(); }
  requestAnimationFrame(animate);
}

// انتخاب مبلغ پیشنهادی
suggestedAmounts.forEach(span => {
  span.addEventListener('click', () => {
    chargeInput.value = span.dataset.amount;
  });
});

// دکمه شارژ → هدایت به درگاه
chargeBtn.addEventListener('click', () => {
  let amount = Number(chargeInput.value);
  if (!amount || amount < 1000) {
    alert('لطفاً مبلغ معتبر وارد کنید (حداقل ۱۰۰۰ تومان)');
    return;
  }

  paymentAmountInput.value = amount;
  paymentForm.submit();
});
function addToWallet(amount){
    walletBalance += amount;
    localStorage.setItem('walletBalance', walletBalance);
    updateWalletDisplay();
}
document.addEventListener('DOMContentLoaded', () => {
  const backBtn = document.getElementById('backToDashboard');
  backBtn.addEventListener('click', () => {
    window.location.href = 'dashbord.html'; // مسیر صفحه داشبورد
  });
});
document.addEventListener('DOMContentLoaded', () => {
    let walletBalance = Number(localStorage.getItem('walletBalance')) || 0;

    const chargeBtn = document.getElementById('chargeBtn');
    const chargeInput = document.getElementById('chargeAmount');

    chargeBtn.addEventListener('click', () => {
        let amount = Number(chargeInput.value);
        if(!amount || amount < 1000){
            alert('لطفاً مبلغ معتبر وارد کنید (حداقل ۱۰۰۰ تومان)');
            return;
        }

        walletBalance += amount;
        localStorage.setItem('walletBalance', walletBalance);
        alert(`کیف پول شما با ${amount.toLocaleString()} تومان شارژ شد!`);
    });
});

