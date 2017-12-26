class Constant:

    setting    = 'PHPMe.sublime-settings'
    in_globals = 'Found in globals'
    in_dir     = 'In same dir'

    gen_getter = 1
    gen_setter = 2
    gen_all    = 1 | 2

    magic_methods = [
        '__construct', '__destruct', '__call', '__callStatic',
        '__get', '&__get', '__set', '__isset', '__unset',
        '__sleep', '__wakeup', '__toString', '__invoke',
        '__set_state', '__clone', '__debugInfo'
    ]

    pass
