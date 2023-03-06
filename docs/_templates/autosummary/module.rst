:orphan:

{{ fullname | escape | underline}}

{% if not modules %}
.. automodule:: {{ fullname }}
    :members:
    :autosummary:
    :autosummary-members:
{% endif %}

{% block members %}
{% if members and modules %}
Public APIs
-----------
.. automodule:: {{ fullname }}
    :members: {% for item in members %} {{ item }}, {%- endfor %}
    :autosummary:
    :autosummary-members:
    :autosummary-no-nesting:
{% endif %}
{% endblock %}

{% block modules %}
{% if modules %}
Subpackages / Submodules
------------------------
.. autosummary::
   :toctree:
   :recursive:
{% for item in modules %}
   {{ item }}
{%- endfor %}
{% endif %}
{% endblock %}
