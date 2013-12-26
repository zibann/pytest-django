import sys
import types

def monkeypatch_method(obj, method_name, new_method):
    assert hasattr(obj, method_name)

    if sys.version_info < (3, 0):
        wrapped_method = types.MethodType(new_method, obj, obj.__class__)
    else:
        wrapped_method = types.MethodType(new_method, obj)

    setattr(obj, method_name, wrapped_method)
