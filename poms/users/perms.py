import time


def test1():
    from poms.accounts.models import Account
    from poms.users.models import MasterUser
    from django.contrib.auth.models import Group, User
    from guardian.shortcuts import assign_perm, get_perms, get_objects_for_user, get_perms_for_model, \
        get_users_with_perms
    from guardian.core import ObjectPermissionChecker

    from django.db import transaction

    with transaction.atomic():
        master_user = MasterUser.objects.all().first()
        acc1, _ = Account.objects.get_or_create(master_user=master_user, name='perms_acc1')
        acc2, _ = Account.objects.get_or_create(master_user=master_user, name='perms_acc2')

        acc1_group, _ = Group.objects.get_or_create(name="acc1_group")
        acc2_group, _ = Group.objects.get_or_create(name="acc2_group")

        assign_perm('change_account', acc1_group, acc1)
        assign_perm('change_account', acc2_group, acc2)

        user1, _ = User.objects.get_or_create(username="user1")
        user2, _ = User.objects.get_or_create(username="user2")

        print('-' * 79)
        print(1, user1.has_perm('change_account', acc1))
        print(2, user1.has_perm('change_account', acc2))
        print(3, user2.has_perm('change_account', acc1))
        print(4, user2.has_perm('change_account', acc2))

        print('-' * 79)
        user1.groups.add(acc1_group)
        print(1, user1.has_perm('change_account', acc1))
        print(2, user1.has_perm('change_account', acc2))
        print(3, user2.has_perm('change_account', acc1))
        print(4, user2.has_perm('change_account', acc2))

        print('-' * 79)
        user2.groups.add(acc2_group)
        print(1, user1.has_perm('change_account', acc1))
        print(2, user1.has_perm('change_account', acc2))
        print(3, user2.has_perm('change_account', acc1))
        print(4, user2.has_perm('change_account', acc2))

        print('-' * 79)
        print(1, get_perms(user1, acc1))
        print(2, get_perms(user1, acc2))
        print(3, get_perms(user2, acc1))
        print(4, get_perms(user2, acc2))

        print('-' * 79)
        print(1, get_objects_for_user(user1, 'accounts.change_account'))
        print(2, get_objects_for_user(user2, 'accounts.change_account'))
        print(3, get_objects_for_user(user1, 'change_account', klass=Account))
        print(4, get_objects_for_user(user2, 'change_account', klass=Account))

        print('-' * 79)
        print(1, get_perms_for_model(Account))
        print(2, get_users_with_perms(acc1))
        print(2, get_users_with_perms(acc2, attach_perms=True))

        print('-' * 79)
        perm_user1 = ObjectPermissionChecker(user1)
        print(1, perm_user1.get_perms(acc1))
        print(2, perm_user1.get_group_perms(acc1))
        print(3, perm_user1.get_user_perms(acc1))
        print(4, perm_user1.get_group_filters(acc1))
        print(5, perm_user1.get_user_filters(acc1))

        print('-' * 79)
        time.sleep(1)
        raise RuntimeError('transaction rollback')


def e1_accounts():
    from poms.accounts.models import Account
    from poms.users.models import MasterUser
    from django.contrib.auth.models import Group, User
    from guardian.shortcuts import assign_perm, get_perms, get_objects_for_user, get_perms_for_model, \
        get_users_with_perms
    from guardian.core import ObjectPermissionChecker

    from django.db import transaction

    with transaction.atomic():
        owner1, _ = User.objects.get_or_create(username="e1:owner1")
        owner2, _ = User.objects.get_or_create(username="e1:owner2")

        mu1, _ = MasterUser.objects.get_or_create(user=owner1)
        mu2, _ = MasterUser.objects.get_or_create(user=owner2)

        mu_grp1, _ = Group.objects.get_or_create(name='e1:MasterUsers:%s' % mu1.pk)
        mu_grp2, _ = Group.objects.get_or_create(name='e1:MasterUsers:%s' % mu2.pk)
        acc_grp1, _ = Group.objects.get_or_create(name='e1:Accounts:%s' % mu1.pk)
        acc_grp2, _ = Group.objects.get_or_create(name='e1:Accounts:%s' % mu2.pk)

        agent1, _ = User.objects.get_or_create(username="e1:agent1")
        agent2, _ = User.objects.get_or_create(username="e1:agent2")
        agent3, _ = User.objects.get_or_create(username="e1:agent3")
        agent4, _ = User.objects.get_or_create(username="e1:agent4")

        owner1.groups = [mu_grp1]
        owner2.groups = [mu_grp2]
        agent1.groups = [acc_grp1]
        agent2.groups = [acc_grp2]
        agent3.groups = [acc_grp1, acc_grp2]
        agent4.groups = []

        acc1, _ = Account.objects.get_or_create(master_user=mu1, name='e1:acc1')
        acc2, _ = Account.objects.get_or_create(master_user=mu2, name='e1:acc2')

        # assign_perm('accounts.change_account', mu_grp1)
        # assign_perm('accounts.change_account', mu_grp2)
        assign_perm('change_account', mu_grp1, acc1)
        assign_perm('change_account', mu_grp2, acc2)
        assign_perm('change_account', acc_grp1, acc1)
        assign_perm('change_account', acc_grp2, acc2)

        # assign_perm('add_account', acc_grp1, mu1)
        # assign_perm('view_accountclassifier', acc_grp1, mu1)

        pc_owner1 = ObjectPermissionChecker(owner1)
        print(1, pc_owner1.get_perms(acc1))

        print('-' * 79)
        print(0, owner1.has_perm('accounts.change_account'))
        print(0, owner2.has_perm('accounts.change_account'))
        print(1, owner1.has_perm('change_account', acc1))
        print(1, owner1.has_perm('change_account', acc2))
        print(2, owner2.has_perm('change_account', acc1))
        print(3, owner2.has_perm('change_account', acc2))

        print('-' * 79)
        print(1, agent1.has_perm('change_account', acc1))
        print(2, agent1.has_perm('change_account', acc2))
        print(3, agent2.has_perm('change_account', acc1))
        print(4, agent2.has_perm('change_account', acc2))
        print(5, agent3.has_perm('change_account', acc1))
        print(6, agent3.has_perm('change_account', acc2))
        print(7, agent4.has_perm('change_account', acc1))
        print(8, agent4.has_perm('change_account', acc2))

        print('-' * 79)
        accept_global_perms = False
        # print(1, get_objects_for_user(owner1, 'accounts.change_account', accept_global_perms=accept_global_perms))
        # print(2, get_objects_for_user(owner2, 'accounts.change_account', accept_global_perms=accept_global_perms))
        print(3, get_objects_for_user(owner1, 'change_account', klass=Account, accept_global_perms=accept_global_perms))
        print(4, get_objects_for_user(owner2, 'change_account', klass=Account, accept_global_perms=accept_global_perms))

        print('-' * 79)
        print(1, get_objects_for_user(agent1, 'change_account', klass=Account, accept_global_perms=accept_global_perms))
        print(2, get_objects_for_user(agent2, 'change_account', klass=Account, accept_global_perms=accept_global_perms))
        print(3, get_objects_for_user(agent3, 'change_account', klass=Account, accept_global_perms=accept_global_perms))
        print(4, get_objects_for_user(agent4, 'change_account', klass=Account, accept_global_perms=accept_global_perms))

        # how add perms to add account for mu and agent1?
        assign_perm('add_account', mu_grp1, mu1)
        # assign_perm('add_account', mu_grp1, agent1)

        print('-' * 79)
        time.sleep(1)
        raise RuntimeError('transaction rollback')


def main():
    import os
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "poms_app.settings")
    import django
    django.setup()

    # test1()
    e1_accounts()


if __name__ == "__main__":
    main()
