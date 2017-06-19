echo "all"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel -a -o ~/tmp/all.png

echo "accounts"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel accounts -o ~/tmp/accounts.png

echo "audit"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel audit -o ~/tmp/audit.png

echo "chats"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel chats -o ~/tmp/chats.png

echo "counterparties"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel counterparties -o ~/tmp/counterparties.png

echo "currencies"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel currencies -o ~/tmp/currencies.png

echo "http_sessions"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel http_sessions -o ~/tmp/http_sessions.png

echo "instruments"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel instruments -o ~/tmp/instruments.png

echo "integrations"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel integrations -o ~/tmp/integrations.png

echo "notifications"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel notifications -o ~/tmp/notifications.png

echo "obj_attrs"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel obj_attrs -o ~/tmp/obj_attrs.png

echo "obj_perms"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel obj_perms -o ~/tmp/obj_perms.png

echo "portfolios"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel portfolios -o ~/tmp/portfolios.png

echo "strategies"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel strategies -o ~/tmp/strategies.png

echo "tags"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel tags -o ~/tmp/tags.png

echo "transactions"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel transactions -o ~/tmp/transactions.png

echo "ui"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel ui -o ~/tmp/ui.png

echo "users"
./manage_ai.py graph_models -X NamedModel,TimeStampedModel users -o ~/tmp/users.png

echo "done"
