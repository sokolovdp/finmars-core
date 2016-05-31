echo "all"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase -a -o ~/tmp/all.png

echo "chats"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase chats  -o ~/tmp/chats.png

echo "users"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase users  -o ~/tmp/users.png

echo "accounts"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase accounts  -o ~/tmp/accounts.png

echo "counterparties"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase counterparties  -o ~/tmp/counterparties.png

echo "currencies"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase currencies  -o ~/tmp/currencies.png

echo "instruments"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase instruments  -o ~/tmp/instruments.png

echo "portfolios"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase portfolios  -o ~/tmp/portfolios.png

echo "transactions"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase transactions  -o ~/tmp/transactions.png

echo "tags"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase tags  -o ~/tmp/tags.png

echo "ui"
./manage.py graph_models -X NamedModel,TimeStampedModel,TagModelBase,ClassModelBase,ObjectPermissionBase,AttributeTypeOptionBase,AttributeBase,AttributeTypeOptionBase ui  -o ~/tmp/ui.png

echo "done"
