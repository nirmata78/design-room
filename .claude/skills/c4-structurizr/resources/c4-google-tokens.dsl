styles {
    element "Element" {
        shape RoundedBox
        width 400
        height 220
        fontSize 30
        strokeWidth 2
        metadata false
        description true
    }
    element "Person" {
        shape Person
        background #174EA6
        color #FFFFFF
        stroke #174EA6
        width 340
        height 280
    }
    element "Software System" {
        background #4285F4
        color #FFFFFF
        stroke #1967D2
    }
    element "Container" {
        background #8AB4F8
        color #202124
        stroke #1967D2
    }
    element "Database" {
        shape Cylinder
        background #188038
        color #FFFFFF
        stroke #188038
    }
    element "Queue" {
        shape Pipe
        background #F8F9FA
        color #202124
        stroke #202124
    }
    element "Cache" {
        background #FEF7E0
        color #202124
        stroke #FBBC05
    }
    element "Component" {
        shape RoundedBox
        background #E8F0FE
        color #202124
        stroke #4285F4
    }
    element "External" {
        background #5F6368
        color #FFFFFF
        stroke #3C4043
    }
    element "New" {
        stroke #FBBC05
        strokeWidth 6
    }
    element "Breaks" {
        background #EA4335
        color #FFFFFF
        stroke #C5221F
    }
    element "Fix" {
        background #34A853
        color #FFFFFF
        stroke #188038
    }
    element "Boundary" {
        stroke #9AA0A6
        color #202124
        border dashed
        strokeWidth 2
        fontSize 28
        metadata false
        background #F8F9FA
    }

    relationship "Relationship" {
        thickness 3
        color #5F6368
        routing Orthogonal
        jump true
        fontSize 28
        width 220
    }
    relationship "HTTPS" {
        color #202124
        style solid
        thickness 3
    }
    relationship "Sync" {
        color #202124
        style solid
        thickness 3
    }
    relationship "Event" {
        color #1967D2
        style dashed
        thickness 3
    }
    relationship "Async" {
        color #1967D2
        style dashed
        thickness 3
    }
    relationship "File" {
        color #5F6368
        style dashed
        thickness 3
    }
    relationship "Batch" {
        color #5F6368
        style dashed
        thickness 3
    }
    relationship "Response" {
        color #188038
        style dashed
        thickness 3
    }
    relationship "Internal" {
        color #5F6368
        style solid
        thickness 3
    }
}
