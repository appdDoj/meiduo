from rest_framework import serializers

from . models import Area


class AreasSerializer(serializers.ModelSerializer):
    """省级数据的序列化器：只做序列化
    list
    """
    class Meta:
        model = Area
        fields = ['id', 'name']


class SubsAreasSerializer(serializers.ModelSerializer):
    """城市或者区县数据的序列化器：只做序列化
    retrieve
    """

    # 关联AreasSerializer
    # subs 里面的数据，来源于关联的序列化器序列化之后的结果
    subs = AreasSerializer(many=True, read_only=True)

    class Meta:
        model = Area
        fields = ['id', 'name', 'subs']
