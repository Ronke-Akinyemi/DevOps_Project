from rest_framework import serializers

class AdminInviteSerializer(serializers.Serializer):
    def validate(self, attrs):
        if not 'email' in attrs.keys():
            raise serializers.ValidationError(
                "Email must be provided")
        return attrs
    email = serializers.EmailField()
    firstname = serializers.CharField()
    lastname = serializers.CharField()
    # role = serializers.ChoiceField(
    #     choices=["Administrator", "Accountant", "Customer-support", "Loan-manager"], required=False)