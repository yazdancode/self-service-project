from django.contrib.auth import login, logout
from django.shortcuts import redirect, render
from django.views import View

from .forms import CustomAuthenticationForm, RegisterForm


class LoginView(View):
    template_name = "accounts/login.html"

    def get(self, request):
        form = CustomAuthenticationForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = CustomAuthenticationForm(request.POST, request=request)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            return redirect("menu:menu")
        return render(request, self.template_name, {"form": form})


class LogoutView(View):
    @staticmethod
    def get(request):
        logout(request)
        return redirect("accounts:login")


class RegisterView(View):
    template_name = "accounts/register.html"

    def get(self, request):
        form = RegisterForm()
        return render(request, self.template_name, {"form": form})

    def post(self, request):
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data["password"])
            user.role = form.user_type
            user.save()
            login(request, user)
            return redirect("accounts:login")
        return render(request, self.template_name, {"form": form})
