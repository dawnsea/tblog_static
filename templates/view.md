{% extends "layout.html" %}
{% block body %}
    {% if post %}
        <div class=title>{{ post.subject }}</div>
        <div class=date>{{ post.date }}</div>
        <div class=content>{{ post.text.decode('utf-8') }}</div>
        <div class=tag>
        {% if post.tags %}
          #
        {% endif %}
        {% for item in post.tags %}
        <a href="{{ url_for('tag_list', tag=item.strip()) }}">{{ item.strip() }}/</a> 
        {% endfor %}</div>
        
        <script>
            function del_ok() {
                if (confirm('삭제?')) {
                    document.location.href="{{ url_for('delete_entry', year=post.year, month=post.month, filename=post.filename) }}";
                }                
            }
        </script>
        <div class=ed>
            <a href="{{ url_for('edit_entry', year=post.year, month=post.month, filename=post.filename) }}">edit</a>
            <a href="#" onclick="del_ok()">delete</a>
        </div>

    {% endif %}            
  
  
{% endblock %}
