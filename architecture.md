graph TD
    %% Server and Docker
    D1(Dockerfile)
    D2(docker-compose.yml)
    S(social_server.py)
    DB[(Database)]

    %% API Layer (Routes)
    R1(routes/social_linkedin.py)
    R2(routes/social_instagram.py)
    R3(routes/social_twitter.py)
    R4(routes/social_routes.py)

    %% Services
    S1(services/linkedin.py)
    S2(services/instagram.py)
    S3(services/twitter.py)
    S4(services/database.py)
    S5(services/youtube.py)

    %% Models
    M1(models/linkedin.py)
    M2(models/instagram.py)
    M3(models/twitter.py)
    M4(models/youtube.py)

    %% Agents
    A1(agents_all/linkedin_agents.py)
    A2(agents_all/youtube_agents.py)
    A3(agents_all/instagram_agents.py)
    A4(agents_all/twitter_agents.py)

    %% Docker orchestration
    D2 --> S
    S --> D1

    %% Server to routes
    S --> R1
    S --> R2
    S --> R3
    S --> R4

    %% Routes to services
    R1 --> S1
    R2 --> S2
    R3 --> S3
    R4 --> S4
    R4 --> S5

    %% Services to models
    S1 --> M1
    S2 --> M2
    S3 --> M3
    S4 --> M1
    S4 --> M2
    S4 --> M3
    S4 --> M4
    S5 --> M4

    %% Services to agents
    S1 --> A1
    S2 --> A3
    S3 --> A4
    S5 --> A2

    %% Agents to models
    A1 --> M1
    A2 --> M4
    A3 --> M2
    A4 --> M3

    %% Database connection
    S4 --> DB