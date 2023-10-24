if [[ $PY311 == 1 ]]
then
    mkdir -p ./pydoc
    touch ./pydoc/__init__.py
    cat <<EOF > ./pydoc/__init__.py
def get_doc(*args):
    return ''
EOF
    mkdir -p ./webbrowser
    touch ./webbrowser/__init__.py
    cat <<EOF > ./webbrowser/__init__.py
EOF
    git apply python311.patch
    echo patch applied
fi
