from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views import generic

from diary.forms import EntryForm, RegisterForm
from diary.models import Entry


class EntryListView(LoginRequiredMixin, generic.ListView):
    """Список записей + поиск по заголовку и содержимому."""

    template_name = 'diary/entry_list.html'
    context_object_name = 'entries'
    paginate_by = 6

    def get_queryset(self):
        queryset = Entry.objects.select_related('owner')
        if not self.request.user.has_perm('diary.view_all_entries'):
            queryset = queryset.filter(owner=self.request.user)
        search = self.request.GET.get('q', '').strip()
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(content__icontains=search),
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search'] = self.request.GET.get('q', '')
        return context


class EntryDetailView(LoginRequiredMixin, generic.DetailView):
    """Детальный просмотр: автор или модератор."""

    template_name = 'diary/entry_detail.html'

    def get_queryset(self):
        if self.request.user.has_perm('diary.view_all_entries'):
            return Entry.objects.all()
        return Entry.objects.filter(owner=self.request.user)


class EntryCreateView(LoginRequiredMixin, generic.CreateView):
    template_name = 'diary/entry_form.html'
    form_class = EntryForm
    success_url = reverse_lazy('diary:entry_list')

    def form_valid(self, form):
        form.instance.owner = self.request.user
        messages.success(self.request, 'Запись добавлена.')
        return super().form_valid(form)


class EntryUpdateView(LoginRequiredMixin, generic.UpdateView):
    """Редактирование — только свои записи."""

    template_name = 'diary/entry_form.html'
    form_class = EntryForm

    def get_queryset(self):
        return Entry.objects.filter(owner=self.request.user)

    def form_valid(self, form):
        messages.success(self.request, 'Запись обновлена.')
        return super().form_valid(form)


class EntryDeleteView(LoginRequiredMixin, generic.DeleteView):
    """Удаление — только свои записи."""

    template_name = 'diary/entry_confirm_delete.html'
    success_url = reverse_lazy('diary:entry_list')

    def get_queryset(self):
        return Entry.objects.filter(owner=self.request.user)


class RegisterView(generic.CreateView):
    template_name = 'registration/register.html'
    form_class = RegisterForm
    success_url = reverse_lazy('diary:entry_list')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        messages.success(self.request, 'Добро пожаловать в ваш дневник!')
        return redirect('diary:entry_list')
