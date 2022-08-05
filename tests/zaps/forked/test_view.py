def test_params(zap, base_swap, base_token):
    if hasattr(zap, "base_pool"):
        assert zap.base_pool() == base_swap
        assert zap.base_token() == base_token
