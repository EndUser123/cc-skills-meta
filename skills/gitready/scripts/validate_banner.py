#!/usr/bin/env python
"""
validate_banner.py - Banner Quality Validation with Z.ai Vision API

Validates generated banner images for:
1. Basic properties (dimensions, file size, corruption)
2. Visual quality using Z.ai Vision API
3. Content validation (text readability, branding, professionalism)

Usage:
    python validate_banner.py <banner_path> [--zai-key KEY]
    python validate_banner.py assets/banners/myproject_banner.png
    python validate_banner.py assets/banners/myproject_banner.png --zai-key $Z_AI_API_KEY

Environment:
    Z_AI_API_KEY - Z.ai API key (or pass via --zai-key)
"""

import argparse
import base64
import os
import sys
from pathlib import Path
from typing import Any

import httpx
from PIL import Image


class Colors:
    """ANSI color codes for terminal output."""

    BLUE = "\033[0;34m"
    GREEN = "\033[0;32m"
    YELLOW = "\033[1;33m"
    RED = "\033[0;31m"
    NC = "\033[0m"  # No Color


def log_info(msg: str) -> None:
    """Print info message."""
    print(f"{Colors.BLUE}[INFO]{Colors.NC} {msg}")


def log_success(msg: str) -> None:
    """Print success message."""
    print(f"{Colors.GREEN}[✓]{Colors.NC} {msg}")


def log_warning(msg: str) -> None:
    """Print warning message."""
    print(f"{Colors.YELLOW}[!]{Colors.NC} {msg}")


def log_error(msg: str) -> None:
    """Print error message."""
    print(f"{Colors.RED}[✗]{Colors.NC} {msg}")


class BannerValidator:
    """Validates banner image quality using basic checks and Z.ai Vision API."""

    # Banner specifications (GitHub social preview standard)
    REQUIRED_WIDTH = 1200
    REQUIRED_HEIGHT = 630
    MIN_FILE_SIZE = 10_000  # 10KB
    MAX_FILE_SIZE = 500_000  # 500KB

    # Z.ai API configuration
    ZAI_API_URL = "https://api.z.ai/api/anthropic/v1/messages"
    ZAI_MODEL = "claude-sonnet-4-20250514"
    ZAI_VERSION = "2023-06-01"
    ZAI_MAX_TOKENS = 1000

    def __init__(self, zai_api_key: str | None = None):
        """Initialize banner validator.

        Args:
            zai_api_key: Z.ai API key. If None, reads from Z_AI_API_KEY env var.
        """
        self.zai_api_key = zai_api_key or os.getenv("Z_AI_API_KEY")
        if not self.zai_api_key:
            log_warning("Z_AI_API_KEY not set - vision analysis will be skipped")

    def validate_basic_properties(self, banner_path: Path) -> dict[str, Any]:
        """Validate basic banner properties.

        Args:
            banner_path: Path to banner image.

        Returns:
            Dictionary with validation results.
        """
        log_info("=== Basic Property Validation ===")

        results = {
            "path": str(banner_path),
            "exists": False,
            "readable": False,
            "dimensions_correct": False,
            "size_correct": False,
            "not_corrupted": False,
            "errors": [],
            "warnings": [],
        }

        # Check if file exists
        if not banner_path.exists():
            results["errors"].append(f"File not found: {banner_path}")
            log_error(f"File not found: {banner_path}")
            return results

        results["exists"] = True
        log_success(f"File exists: {banner_path}")

        # Check file size
        file_size = banner_path.stat().st_size
        results["file_size"] = file_size

        if file_size < self.MIN_FILE_SIZE:
            results["warnings"].append(
                f"File too small: {file_size} bytes (min: {self.MIN_FILE_SIZE})"
            )
            log_warning(
                f"File too small: {file_size} bytes (min: {self.MIN_FILE_SIZE})"
            )
        elif file_size > self.MAX_FILE_SIZE:
            results["errors"].append(
                f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})"
            )
            log_error(f"File too large: {file_size} bytes (max: {self.MAX_FILE_SIZE})")
        else:
            results["size_correct"] = True
            log_success(f"File size: {file_size:,} bytes")

        # Check if image is readable and get dimensions
        try:
            with Image.open(banner_path) as img:
                width, height = img.size
                results["width"] = width
                results["height"] = height
                results["dimensions"] = f"{width}x{height}"
                results["not_corrupted"] = True
                results["readable"] = True

                if width == self.REQUIRED_WIDTH and height == self.REQUIRED_HEIGHT:
                    results["dimensions_correct"] = True
                    log_success(f"Dimensions: {width}x{height} (correct)")
                else:
                    results["errors"].append(
                        f"Wrong dimensions: {width}x{height} (expected: {self.REQUIRED_WIDTH}x{self.REQUIRED_HEIGHT})"
                    )
                    log_error(
                        f"Wrong dimensions: {width}x{height} (expected: {self.REQUIRED_WIDTH}x{self.REQUIRED_HEIGHT})"
                    )

                # Get format info
                results["format"] = img.format
                results["mode"] = img.mode
                log_info(f"Format: {img.format}, Mode: {img.mode}")

        except Exception as e:
            results["errors"].append(f"Cannot read image: {e}")
            results["not_corrupted"] = False
            log_error(f"Cannot read image: {e}")

        return results

    def validate_with_vision_api(self, banner_path: Path) -> dict[str, Any]:
        """Validate banner using Z.ai Vision API.

        Args:
            banner_path: Path to banner image.

        Returns:
            Dictionary with vision analysis results.
        """
        log_info("=== Z.ai Vision Analysis ===")

        results = {
            "analyzed": False,
            "quality_score": None,
            "feedback": "",
            "issues": [],
            "recommendations": [],
        }

        if not self.zai_api_key:
            results["feedback"] = "Skipped - Z_AI_API_KEY not configured"
            log_warning("Skipped - Z_AI_API_KEY not configured")
            return results

        # Encode image as base64
        try:
            with open(banner_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")
        except Exception as e:
            results["feedback"] = f"Failed to read image: {e}"
            log_error(f"Failed to read image: {e}")
            return results

        # Prepare request
        headers = {
            "x-api-key": self.zai_api_key,
            "anthropic-version": self.ZAI_VERSION,
            "content-type": "application/json",
        }

        prompt = """Analyze this banner image for GitHub repository social preview.

Rate the banner on a scale of 1-10 for each criterion:
1. **Text Readability** - Is text clear and high contrast?
2. **Professionalism** - Does it look polished and intentional?
3. **Branding** - Does it clearly communicate the package name?
4. **Visual Appeal** - Are colors, layout, and design pleasing?

Provide:
- Overall quality score (1-10)
- Specific issues found (if any)
- Recommendations for improvement

Respond in this format:
SCORE: X/10
ISSUES: [list any issues]
RECOMMENDATIONS: [list any suggestions]
FEEDBACK: [brief overall assessment]"""

        payload = {
            "model": self.ZAI_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image",
                            "source": {
                                "type": "base64",
                                "media_type": "image/png",
                                "data": image_data,
                            },
                        },
                        {"type": "text", "text": prompt},
                    ],
                }
            ],
            "max_tokens": self.ZAI_MAX_TOKENS,
        }

        # Call Z.ai API
        try:
            log_info("Calling Z.ai Vision API...")
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    self.ZAI_API_URL,
                    headers=headers,
                    json=payload,
                )

                if response.status_code == 200:
                    data = response.json()

                    # Extract text content from Anthropic format
                    content = ""
                    for block in data.get("content", []):
                        if block.get("type") == "text":
                            content += block.get("text", "")

                    results["analyzed"] = True
                    results["feedback"] = content

                    # Parse structured response
                    for line in content.split("\n"):
                        if line.startswith("SCORE:"):
                            try:
                                score_str = line.split(":")[1].strip().split("/")[0]
                                results["quality_score"] = int(score_str)
                                log_success(f"Quality Score: {score_str}/10")
                            except (ValueError, IndexError):
                                pass
                        elif line.startswith("ISSUES:"):
                            issues = line.split(":", 1)[1].strip()
                            if issues and issues != "[]":
                                results["issues"] = [
                                    i.strip("- ") for i in issues.split(",")
                                ]
                        elif line.startswith("RECOMMENDATIONS:"):
                            recs = line.split(":", 1)[1].strip()
                            if recs and recs != "[]":
                                results["recommendations"] = [
                                    r.strip("- ") for r in recs.split(",")
                                ]

                else:
                    results["feedback"] = f"API Error: HTTP {response.status_code}"
                    log_error(f"API Error: HTTP {response.status_code}")
                    log_error(f"Response: {response.text[:200]}")

        except httpx.TimeoutException:
            results["feedback"] = "API timeout (30s)"
            log_error("API timeout (30s)")
        except Exception as e:
            results["feedback"] = f"API Error: {e}"
            log_error(f"API Error: {e}")

        return results

    def validate(self, banner_path: Path) -> dict[str, Any]:
        """Run full validation on banner.

        Args:
            banner_path: Path to banner image.

        Returns:
            Complete validation results.
        """
        log_info(f"=== Banner Validation: {banner_path} ===")

        basic_results = self.validate_basic_properties(banner_path)
        vision_results = self.validate_with_vision_api(banner_path)

        # Combine results
        overall_pass = (
            basic_results.get("dimensions_correct", False)
            and basic_results.get("size_correct", False)
            and basic_results.get("not_corrupted", False)
            and len(basic_results.get("errors", [])) == 0
        )

        return {
            "overall_pass": overall_pass,
            "basic": basic_results,
            "vision": vision_results,
        }

    def print_report(self, results: dict[str, Any]) -> None:
        """Print validation report.

        Args:
            results: Validation results from validate().
        """
        print()
        log_info("=== Validation Summary ===")

        basic = results["basic"]
        vision = results["vision"]

        # Basic properties
        if basic.get("dimensions_correct"):
            log_success(f"Dimensions: {basic.get('dimensions', 'N/A')}")
        else:
            log_error(f"Dimensions: {basic.get('dimensions', 'N/A')} (incorrect)")

        if basic.get("size_correct"):
            log_success(f"File Size: {basic.get('file_size', 0):,} bytes")
        else:
            log_warning(
                f"File Size: {basic.get('file_size', 0):,} bytes (out of range)"
            )

        # Vision analysis
        if vision.get("analyzed"):
            score = vision.get("quality_score")
            if score is not None:
                if score >= 8:
                    log_success(f"Quality Score: {score}/10 (Excellent)")
                elif score >= 6:
                    log_warning(f"Quality Score: {score}/10 (Good)")
                else:
                    log_error(f"Quality Score: {score}/10 (Needs improvement)")

            if vision.get("issues"):
                log_warning("Issues found:")
                for issue in vision["issues"]:
                    print(f"  - {issue}")

            if vision.get("recommendations"):
                log_info("Recommendations:")
                for rec in vision["recommendations"]:
                    print(f"  - {rec}")

        # Overall verdict
        print()
        if results["overall_pass"]:
            log_success("Banner validation PASSED")
        else:
            log_error("Banner validation FAILED")

        if basic.get("errors"):
            print()
            log_error("Critical Errors:")
            for error in basic["errors"]:
                print(f"  - {error}")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate banner image quality using Z.ai Vision API"
    )
    parser.add_argument(
        "banner_path",
        type=Path,
        help="Path to banner image file",
    )
    parser.add_argument(
        "--zai-key",
        help="Z.ai API key (or set Z_AI_API_KEY env var)",
    )
    parser.add_argument(
        "--fail-on-issues",
        action="store_true",
        help="Exit with error code if validation fails",
    )

    args = parser.parse_args()

    banner_path = args.banner_path.resolve()

    # Validate
    validator = BannerValidator(zai_api_key=args.zai_key)
    results = validator.validate(banner_path)

    # Print report
    validator.print_report(results)

    # Exit code
    if args.fail_on_issues and not results["overall_pass"]:
        sys.exit(1)

    sys.exit(0)


if __name__ == "__main__":
    main()
