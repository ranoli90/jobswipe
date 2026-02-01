graph TD
    subgraph Mobile App (Flutter)
        A[JobSwipe Mobile App]
        B[BLoC State Management]
        C[Dio HTTP Client]
        D[Hive Local Storage]
        E[Flutter Secure Storage]
        F[Firebase Services]
        
        A --> B
        B --> C
        B --> D
        B --> E
        B --> F
        
        subgraph iOS Platform
            G[APNs Push Notifications]
            H[ARKit for AR Features]
            I[Core ML for Local Processing]
        end
        
        subgraph Android Platform
            J[FCM Push Notifications]
            K[ARCore for AR Features]
            L[TensorFlow Lite]
        end
        
        A --> G
        A --> H
        A --> I
        A --> J
        A --> K
        A --> L
    end
    
    subgraph Backend API (FastAPI)
        M[API Layer]
        N[Service Layer]
        O[Data Access Layer]
        P[Background Workers]
        
        M --> N
        N --> O
        M --> P
        
        subgraph Authentication & Security
            Q[JWT/OAuth2]
            R[MFA]
            S[PII Encryption]
            T[Rate Limiting]
        end
        
        subgraph Services
            U[Auth Service]
            V[Job Matching]
            W[Application Automation]
            X[Analytics]
            Y[Notifications]
            Z[Profile Management]
        end
        
        N --> U
        N --> V
        N --> W
        N --> X
        N --> Y
        N --> Z
        
        U --> Q
        U --> R
        O --> S
        M --> T
    end
    
    subgraph Infrastructure (Fly.io)
        AA[PostgreSQL]
        BB[Redis]
        CC[RabbitMQ]
        DD[Ollama AI]
        EE[Prometheus/Grafana]
        FF[Jaeger Tracing]
        GG[OpenSearch]
        
        O --> AA
        T --> BB
        P --> CC
        V --> DD
        X --> EE
        FF --> M
        X --> GG
    end
    
    C --> M
```
