class VariableLengthIDAdapter(Adapter):
    """
    Controlbox Variable Length ID
    """
    def __init__(self):
        super(VariableLengthIDAdapter, self).__init__(RepeatUntil(lambda obj, lst, ctx: obj & 0xF0 == 0x00, Byte))

    def _encode(self, obj, context):
        rewritten_list = []
        for idx, i in enumerate(obj):
            if idx != len(obj)-1:
                rewritten_list.append(i | 0x80)
            else:
                rewritten_list.append(i)

        return rewritten_list

    def _decode(self, obj, context):
        return list(map(lambda x: x & 0x0F, obj))
