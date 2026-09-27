# Python and Django source contracts

Check installed versions before adapting an example. This starter pins Django
6.1 and Python 3.14 in its lockfiles. Examples in this skill illustrate boundaries;
provider clients, queues and domain models shown in examples are not installed
application features.

- [Django model validation](https://docs.djangoproject.com/en/6.1/ref/models/instances/#validating-objects): save does not call full_clean.
- [QuerySet API](https://docs.djangoproject.com/en/6.1/ref/models/querysets/): bulk writes bypass model save and save signals.
- [Transactions](https://docs.djangoproject.com/en/6.1/topics/db/transactions/): on_commit follows commit; durable delivery requires an outbox or equivalent.
- [Forms](https://docs.djangoproject.com/en/6.1/topics/forms/modelforms/): explicit fields and validation boundaries.
- [Authentication](https://docs.djangoproject.com/en/6.1/topics/auth/default/): authentication, permissions and session lifecycle.
- [Python contextvars](https://docs.python.org/3.14/library/contextvars.html): scoped values and token restoration.
- [Python dataclasses](https://docs.python.org/3.14/library/dataclasses.html): explicit value objects.
- [Python logging](https://docs.python.org/3.14/library/logging.html): bounded structured context and exception causes.

The framework and taxonomy originate in Vladimir Dementyev’s *Layered Design for
Ruby on Rails Applications* and the Layered Rails skill distributed by
rails-template. Original files, mapping and patch are recorded in
config/skills-lock.json and third_party/skills at the repository root.
