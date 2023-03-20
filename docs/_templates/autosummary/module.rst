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
APIs
----

For accessing these APIs, you may use import like this:

.. code-block:: python

    from {{ fullname }} import <api_to_import>

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
