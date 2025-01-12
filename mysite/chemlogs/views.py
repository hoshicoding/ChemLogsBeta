from django.http import Http404, HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.template import loader
from django.urls import reverse
from django.views.generic import ListView
from django.db.models import Q
from django.utils import timezone
from .models import Chemical, Transaction, TransactionEdit, Container
from .forms import TransactionEditForm, TransactionCreateForm, ContainerOverrideForm, ContainerCreateForm, ChemicalCreateForm, StateEditForm
import itertools
from django.contrib.auth import get_user_model


# unused
def testPage(request, chemical_id):
    chemical = get_object_or_404(Chemical, pk=chemical_id)
    return render(request, 'chemlogs/testPage.html', {'chemical': chemical})

# main page for a chemical
def chemical(request, chemical_id):
    chemical = get_object_or_404(Chemical, pk=chemical_id)
    container_create_form = None
    chemical_edit_form = None
    state_edit_form = None
    new_container_id = None
    if request.method == 'POST' and 'new_container' in request.POST:
        container_create_form = ContainerCreateForm(request.POST)
        if container_create_form.is_valid():
            if container_create_form.cleaned_data['contents'] == "N":
                # create a new state for this new container
                chemical_state = chemical.chemicalstate_set.create(
                    state=container_create_form.cleaned_data['state'],
                    type=container_create_form.cleaned_data['type'],
                    min_thresh=container_create_form.cleaned_data['min_thresh']
                )
                # TODO: what if user tries to make a state that's equivalent to a preexisting state
            else:
                # find chemicalstate from form's 'contents' field, which stores either state or type.
                # state_list will either be empty or have 1 entry which is the chemicalstate
                # try to find chemicalstate from state
                state_list = chemical.chemicalstate_set.filter(
                    state=container_create_form.cleaned_data['contents']
                )
                if len(state_list) == 0: # can you just say !chemical_state?
                    # override state_list, finding from type
                    state_list = chemical.chemicalstate_set.filter(
                        type=container_create_form.cleaned_data['contents']
                    )
                chemical_state = state_list[0]

            # give the bottle an id.
            # look through AA, AB, ..., AZ, BA, ..., ZZ until you find an unused id
            start = ord("A")
            alphabet_length = 26
            end = start + alphabet_length
            letters_ascii = range(start, end)
            bad_ids = [ # no container should have an id from this list
                # confusion with aqueous
                "AQ",
                # confusion with location
                "MS", "US",
                # confusion with chemical formula
                "HF", "HI", "KH", "KF", "KI"
            ]
            for i, j in itertools.product(letters_ascii, letters_ascii): # this avoids nested for loops
                potential_id = chr(i) + chr(j)
                if len(Container.objects.filter(id=potential_id)) == 0 and potential_id not in bad_ids:
                    container_id = potential_id
                    break
            
            new_container = chemical_state.container_set.create(
                initial_value=container_create_form.cleaned_data['initial_value'],
                contents=container_create_form.cleaned_data['contents'],
                loc=container_create_form.cleaned_data['loc'],
                id=container_id
            )
            if container_create_form.cleaned_data['molarity']:
                new_container.molarity = container_create_form.cleaned_data['molarity']
                new_container.save() # i think that's necessary but haven't tested without it
            # create an N transaction
            new_container.transaction_set.create(
                type="N",
                amount=container_create_form.cleaned_data['initial_value'],
                time=timezone.now(),
                user=request.user
            )
            new_container_id = new_container.id
    if request.method == 'POST' and 'delete_chemical_anyway' in request.POST:
        chemical.delete()
        return redirect('/chemlogs/chemicalSearch/')
    if request.method == 'POST' and 'edit_chemical' in request.POST:
        chemical_edit_form = ChemicalCreateForm(request.POST)
        if chemical_edit_form.is_valid():
            chemical.name=chemical_edit_form.cleaned_data['name']
            chemical.cas=chemical_edit_form.cleaned_data['cas']
            if chemical_edit_form.cleaned_data['safety']:
                chemical.safety=chemical_edit_form.cleaned_data['safety']
            chemical.formula=chemical_edit_form.cleaned_data['formula']
            if chemical_edit_form.cleaned_data['molar_mass']:
                chemical.molar_mass=chemical_edit_form.cleaned_data['molar_mass']
            chemical.save() # is this line necessary?
    if request.method == 'POST':
        for state in chemical.chemicalstate_set.all():
            possible_name = 'delete_state_anyway_' + str(state.id)
            if possible_name in request.POST:
                state.delete()
                break
        for state in chemical.chemicalstate_set.all():
            possible_name = 'edit_state_' + str(state.id)
            if possible_name in request.POST:
                state_edit_form = StateEditForm(request.POST)
                if state_edit_form.is_valid():
                    state.state = state_edit_form.cleaned_data['state']
                    state.type = state_edit_form.cleaned_data['type']
                    state.save()
                break
    if not container_create_form:
        ContainerCreateForm.contents_choices = [
            ("N", "Add New")
        ]
        for state in chemical.chemicalstate_set.all():
            if not state.type:
                to_append = state.state
            else:
                to_append = state.type
            ContainerCreateForm.contents_choices.append((to_append, to_append))
        container_create_form = ContainerCreateForm()
    if not chemical_edit_form:
        # reusing chemical create form to edit chemical. form is autopopulated with existing data.
        chemical_edit_form = ChemicalCreateForm(initial={
            'name': chemical.name,
            'cas': chemical.cas,
            'safety': chemical.safety,
            'formula': chemical.formula,
            'molar_mass': chemical.molar_mass,
            'dangerous': chemical.dangerous
        })
    if not state_edit_form:
        # reusing state create form to edit state. form is autopopulated with existing data.
        state_edit_form = StateEditForm()

    return render(request, 'chemlogs/chemical.html',
                  {'chemical': chemical, 'container_create_form': container_create_form,
                   'chemical_edit_form': chemical_edit_form, 'state_edit_form': state_edit_form,
                   'new_container_id': new_container_id})

def testChem(request, chemical_id):
    chemical = get_object_or_404(Chemical, pk=chemical_id)
    return render(request, 'chemlogs/testChem.html', {'chemical': chemical})

# view and modify a transaction
def transaction(request, transaction_id):
    transaction = get_object_or_404(Transaction, pk=transaction_id)
    edit_form = None
    if request.method == 'POST':
        edit_form = TransactionEditForm(request.POST)
        if edit_form.is_valid():
            new_amount = edit_form.cleaned_data['amount']
            new_type = edit_form.cleaned_data['type']
            # record the change (or don't i guess)
            edit = transaction.transactionedit_set.create(
                date=timezone.now(),
                old_amount=transaction.amount,
                new_amount=new_amount,
                old_type=transaction.type,
                new_type=new_type,
                user=request.user
            )

            # make the change
            transaction.amount = new_amount
            transaction.type = new_type
            transaction.save()
            # there should be a confirmation "are you sure?"
    if not edit_form:
        edit_form = TransactionEditForm(initial={'amount': transaction.amount, 'type': transaction.type})
        edit_form.fields['amount'].label += ' (' + transaction.container.getUnits() + ')'
    return render(request, 'chemlogs/transaction.html', {'transaction': transaction, 'edit_form': edit_form})

def container(request, container_id):
    container = get_object_or_404(Container, pk=container_id)
    transact_form = None
    override_form = None
    if request.method == 'POST':
        if "transact_add" in request.POST:
            transact_form = TransactionCreateForm(request.POST, auto_id='%s')
            if transact_form.is_valid():
                delta = transact_form.cleaned_data['trSlide']
                new_value=container.computeRawAmount() + delta
                if new_value >= 0 and new_value <= container.initial_value:
                    container.transaction_set.create(
                        amount=transact_form.cleaned_data['trSlide'],
                        time=timezone.now(),
                        type="T",
                        user=request.user)
                    # some kind of confirmation ("you have added/removed this much")
                else:
                    # invalidity message
                    pass
        elif "transact_remove" in request.POST:
            transact_form = TransactionCreateForm(request.POST, auto_id='%s')
            if transact_form.is_valid():
                delta = 0 - transact_form.cleaned_data['trSlide']
                new_value=container.computeRawAmount() + delta
                if new_value > 0 and new_value < container.initial_value:
                    container.transaction_set.create(
                        amount=delta,
                        time=timezone.now(),
                        type="T",
                        user=request.user)
                    # add confirmation
                else:
                    # invalidity message
                    pass
        elif "override" in request.POST:
            override_form = ContainerOverrideForm(request.POST, auto_id='%s')
            if override_form.is_valid():
                new_value = override_form.cleaned_data['override_value']
                if new_value > 0 and new_value < container.initial_value:
                    container.transaction_set.create(
                        amount=new_value,
                        time=timezone.now(),
                        type="R",
                        user=request.user)
                    # add confirmation
                else:
                    # invalidity: tell user that the new amount must be within the bottle size and nonnegative
                    pass
        elif "transact_fill" in request.POST:
            container.transaction_set.create(
                amount=container.initial_value,
                time=timezone.now(),
                type="R",
                user=request.user)
            # add confirmation
        elif "transact_empty" in request.POST:
            container.transaction_set.create(
                amount=0,
                time=timezone.now(),
                type="R",
                user=request.user)
            # add confirmation
    if not transact_form:
        transact_form = TransactionCreateForm(auto_id='%s') # this argument makes the input's id "trSlide" rather than "id_trSlide"
    if not override_form:
        override_form = ContainerOverrideForm()
        override_form.fields['override_value'].label += ' (' + container.getUnits() + ')'
    return render(request, 'chemlogs/container.html', {'container': container, 'transact_form': transact_form, 'override_form': override_form})

def delete_account(request, user_id):
    User = get_user_model()
    user = get_object_or_404(User, pk=user_id)
    user.delete()
    return render(request, 'chemlogs/delete_account.html', {'user': user})

# search for chemicals
class ChemicalSearch(ListView):
    model = Chemical
    template_name = 'chemlogs/chemicalSearch.html'
    len_results_displayed = 7 # don't display more results than this

    def get(self, request):
        chemical_create_form = ChemicalCreateForm()
        return render(request, self.template_name, self.get_context_data(chemical_create_form))
    
    def post(self, request):
        chemical_create_form = ChemicalCreateForm(self.request.POST)
        if chemical_create_form.is_valid():
            new_chemical = Chemical.objects.create(
                name=chemical_create_form.cleaned_data['name'],
                cas=chemical_create_form.cleaned_data['cas'],
                formula=chemical_create_form.cleaned_data['formula'])
            if chemical_create_form.cleaned_data['safety']:
                new_chemical.safety=chemical_create_form.cleaned_data['safety']
            if chemical_create_form.cleaned_data['molar_mass']:
                new_chemical.molar_mass=chemical_create_form.cleaned_data['molar_mass']
            new_chemical.save()
        return render(request, self.template_name, self.get_context_data(chemical_create_form))

    def get_context_data(self, chemical_create_form):
        shown_chemicals = self.get_queryset()
        all_shown = len(shown_chemicals) <= ChemicalSearch.len_results_displayed # whether there aren't any hidden matching chemicals
        actions = Transaction.objects.exclude(type="I").order_by('-time')
        return {'shown_chemicals': shown_chemicals, 'all_shown': all_shown, 'actions': actions, 'chemical_create_form': chemical_create_form}

    def get_queryset(self):
        nameSearch = self.request.GET.get("name")
        requireSomeInStock = self.request.GET.get("requireSomeInStock")

        toDisplay = Chemical.objects.all()
        if nameSearch:
            # have to correct for formatting and want to filter by place but it works
            # https://docs.djangoproject.com/en/4.1/topics/db/queries/#complex-lookups-with-q
            # used the above for the OR query, since filter() can't handle it
            toDisplay = toDisplay.filter(Q(name__icontains=nameSearch) | 
                Q(formula__icontains=nameSearch) | Q(cas__icontains=nameSearch))
        if requireSomeInStock:
            toDisplay = [chemical for chemical in toDisplay if ChemicalSearch.inStock(chemical)]
        return toDisplay[:ChemicalSearch.len_results_displayed]
    
    def inStock(chemical):
        for state in chemical.chemicalstate_set.all():
            if state.computeAmount() > 0:
                return True
        return False