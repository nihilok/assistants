>>> Give me a Rust program that monitors a list of IPs/hostnames (e.g. http servers) and checks their status. The server list will be supplied either from a file, or from stdin


Below is a self‑contained example of a simple HTTP‑status monitor in Rust.  It will:

• Read a list of hostnames/IPs (one per line) from either a file (‑f/–file) or stdin  
• Periodically (every N seconds, configurable with ‑i/–interval) issue an HTTP GET to each host (prepends “http://” if you don’t)  
• Print a timestamped report of HTTP status or error  

Save this as `src/main.rs` in a new Cargo project, add the dependencies shown in `Cargo.toml`, then `cargo run …`.

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––  
Cargo.toml  
––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––  
```toml
[package]
name = "http_monitor"
version = "0.1.0"
edition = "2021"

[dependencies]
tokio   = { version = "1.28", features = ["full"] }
reqwest = { version = "0.11", features = ["rustls-tls"] }
clap    = { version = "4.1.8", features = ["derive"] }
chrono  = "0.4"
futures = "0.3"
```

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––  
src/main.rs  
––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––  

```rust
use std::fs::File;
use std::io::{self, BufRead};
use std::path::Path;
use std::time::Duration;

use clap::Parser;
use chrono::Local;
use futures::future::join_all;
use reqwest::Client;
use tokio::time::sleep;

/// Simple HTTP monitor: reads a list of hosts and periodically checks their status.
#[derive(Parser, Debug)]
#[command(author, version, about)]
struct Opt {
    /// Path to file with hosts (one per line). If omitted, reads from stdin.
    #[arg(short, long)]
    file: Option<String>,

    /// Interval between checks in seconds.
    #[arg(short, long, default_value_t = 60)]
    interval: u64,

    /// Request timeout in seconds.
    #[arg(short, long, default_value_t = 10)]
    timeout: u64,
}

#[tokio::main]
async fn main() -> anyhow::Result<()> {
    let opt = Opt::parse();

    // Load hosts
    let hosts = read_hosts(opt.file.as_deref())?;
    if hosts.is_empty() {
        eprintln!("No hosts to monitor. Exiting.");
        return Ok(());
    }

    // Prepare HTTP client with timeout
    let client = Client::builder()
        .timeout(Duration::from_secs(opt.timeout))
        .build()?;

    println!("Monitoring {} hosts every {}s (timeout {}s)…", hosts.len(), opt.interval, opt.timeout);

    loop {
        let timestamp = Local::now().format("%Y-%m-%d %H:%M:%S").to_string();

        // Spawn one future per host
        let checks = hosts.iter().map(|host| {
            let client = client.clone();
            let host = host.clone();
            async move {
                let url = if host.starts_with("http://") || host.starts_with("https://") {
                    host.clone()
                } else {
                    format!("http://{}", host)
                };

                let start = std::time::Instant::now();
                let status = match client.get(&url).send().await {
                    Ok(resp) => format!("HTTP {}", resp.status()),
                    Err(e) => format!("ERROR: {}", e),
                };
                let elapsed = start.elapsed().as_millis();
                (host, url, status, elapsed)
            }
        });

        // Wait for all checks to finish
        let results = join_all(checks).await;

        // Print report
        println!("=== [{}] ===", timestamp);
        for (host, url, status, elapsed) in results {
            println!("{: <30} {: <40} {: <10} {}ms", host, url, status, elapsed);
        }

        // Sleep until next round
        sleep(Duration::from_secs(opt.interval)).await;
    }
}

/// Reads lines from the given file path or stdin, strips comments/whitespace.
fn read_hosts(path: Option<&str>) -> io::Result<Vec<String>> {
    let reader: Box<dyn BufRead> = match path {
        Some(p) => Box::new(io::BufReader::new(File::open(Path::new(p))?)),
        None    => Box::new(io::BufReader::new(io::stdin())),
    };

    let mut hosts = Vec::new();
    for line in reader.lines() {
        let line = line?;
        let trimmed = line.trim();
        if trimmed.is_empty() || trimmed.starts_with('#') {
            continue;
        }
        hosts.push(trimmed.to_string());
    }
    Ok(hosts)
}
```

––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––––  

Example usage:

 1. From a file `hosts.txt`:
    ```
    192.168.1.1
    example.com
    https://rust-lang.org
    ```
    then:
    ```
    cargo run -- --file hosts.txt --interval 30 --timeout 5
    ```

 2. From stdin:
    ```
    cat hosts.txt | cargo run -- --interval 10
    ```

You’ll get a timestamped table every interval showing each host, the URL actually queried, the HTTP status (or error), and the round‑trip time in ms. Feel free to extend it (e.g. add retries, alerting, logging to a file, etc.).